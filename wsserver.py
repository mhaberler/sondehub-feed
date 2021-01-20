
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory, Protocol, Factory
from twisted.protocols import basic
from twisted.internet.endpoints import clientFromString, serverFromString
from twisted.internet.task import LoopingCall
from twisted.application.internet import ClientService, backoffPolicy, StreamServerEndpointService
from twisted.application import internet, service
from twisted.python.log import PythonLoggingObserver, ILogObserver, startLogging, startLoggingWithObserver, addObserver
from twisted.web.server import Site
from twisted.web.resource import Resource

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol, \
    listenWS
from autobahn.websocket.types import ConnectionDeny


import sys
import os
import logging
import logging.handlers as handlers
import syslog
import jsonschema
import bz2
import signal
import setproctitle

import orjson
import argparse
from datetime import datetime, timedelta, timezone
import base64
from collections import Counter
import geojson
import geobuf
#import zmq
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPubConnection, ZmqSubConnection

import boundingbox
from jwt import InvalidAudienceError, ExpiredSignatureError, InvalidSignatureError, PyJWTError
from jwtauth import *

appName = "sonde-server"
defaultLoglevel = 'INFO'
defaultLogDir = "/var/log/sonde-server"
defaultLogDir = "/tmp"
facility = syslog.LOG_LOCAL1
pubSocket = "ipc:///tmp/adsb-json-feed"

PING_EVERY = 30 # secs for now

def client_updater(flight_observer,  zmqSocket):
    pass

    # _topic = b'adsb-json'
    #
    # if not feeder_factory.clients and not zmqSocket:
    #     return
    #
    # # BATCH THIS!!
    # obs = flight_observer.getObservations()
    #
    # for icao, o in obs.items():
    #     if not o.isUpdated():
    #         continue
    #     if not o.isPresentable():
    #         continue
    #
    #     lat = o.getLat()
    #     lon = o.getLon()
    #     alt = o.getAltitude()
    #
    #     js = orjson.dumps(o.__geo_interface__, option=orjson.OPT_APPEND_NEWLINE)
    #     if zmqSocket:
    #         zmqSocket.send_multipart([_topic, js])
    #
    #     if not feeder_factory.clients:
    #         continue
    #
    #     pbf = geobuf.encode(o.__geo_interface__)
    #     for client in feeder_factory.clients:
    #         if within(lat, lon, alt, client.bbox):
    #             if isinstance(client, Downstream):
    #                 client.transport.write(js)
    #             if isinstance(client, WSServerProtocol):
    #                 if not client.usr:
    #                     continue
    #                 if client.proto == 'adsb-geobuf':
    #                     client.sendMessage(pbf, True)
    #                 if client.proto == 'adsb-json':
    #                     client.sendMessage(js, False)
    #     o.resetUpdated()


class WSServerProtocol(WebSocketServerProtocol):

    def onConnecting(self, transport_details):
        logging.info(f"WebSocket connecting: {transport_details}")
        self.last_heard = datetime.utcnow().timestamp()


    def doPing(self):
        if self.run:
            self.sendPing()
            #self.factory.pingsSent[self.peer] += 1
            #log.debug(f"Ping sent to {self.peer}")
            reactor.callLater(PING_EVERY, self.doPing)

    def onPong(self, payload):
        #self.factory.pongsReceived[self.peer] += 1
        self.last_heard = datetime.utcnow().timestamp()
        #log.debug(f"Pong received from {self.peer}")


    def onConnect(self, request):
        log.debug(f"Client connecting: {request.peer} version {request.version}")
        log.debug(f"headers: {request.headers}")
        log.debug(f"path: {request.path}")
        log.debug(f"params: {request.params}")
        log.debug(f"protocols: {request.protocols}")
        log.debug(f"extensions: {request.extensions}")
        self.peer = request.peer
        self.usr = None  # until after jwt decoded

        self.bbox = boundingbox.BoundingBox()
        self.bbox.fromParams(request.params)
        self.geobuf = 'options' in request.params and 'geobuf' in request.params['options']
        self.forwarded_for = request.headers.get('x-forwarded-for', '')
        self.host = request.headers.get('host', '')

        self.proto = None
        # server-side preference of subprotocol
        for p in self.factory._subprotocols:
            if p in request.protocols:
                self.proto = p
                break

        if not self.proto:
            raise ConnectionDeny(ConnectionDeny.BAD_REQUEST)

        self.user_agent = request.headers.get('user-agent',"")

        log.debug(f"chosen protocol {self.proto} for {self.forwarded_for} via {self.peer} ua={self.user_agent}")

        if 'token' in request.params:
            try:
                for token in request.params['token']:
                    obj = self.factory.jwt_auth.decodeToken(token)
                    log.debug(f"token={obj} from {self.forwarded_for}")
                    self.usr = obj['usr']
                    finish = min(datetime.utcnow().timestamp() +
                                 obj['dur'], obj['exp'])
                    close_in = round(finish - datetime.utcnow().timestamp())
                    reactor.callLater(int(close_in), self.sessionExpired)
                    log.debug(
                        f"session expires in {close_in} seconds - {datetime.fromtimestamp(finish)}")
                    break

            except PyJWTError as e:
                log.error(f"JWTError  {e}")
                raise ConnectionDeny(1066)


        else:
            log.info(f"no token passed in URI by {self.forwarded_for} via {request.peer}")
            raise ConnectionDeny(1066)

        # accept the WebSocket connection, speaking subprotocol `proto`
        # and setting HTTP headers `headers`
        # return (proto, headers)
        return self.proto

    def sessionExpired(self):
        self.factory.feeder_factory.unregisterClient(self)
        log.debug(f"token validity time exceeded, closing {self.forwarded_for} via {self.peer}")
        self.sendClose()

    def onOpen(self):
        log.debug(f"connection open to {self.forwarded_for} via {self.peer}")
        self.run = True
        self.factory.feeder_factory.registerClient(self)
        self.doPing()


    def onMessage(self, payload, isBinary):
        # if isBinary:
        #     log.debug(f"Binary message received: {len(payload)} bytes")
        # else:
        #     log.debug(f"Text message received: {payload.decode('utf8')}")

        (success, bbox, response) = self.factory.bbox_validator.validate_str(payload)
        if not success:
            log.info(f'{self.peer} bbox update failed: {response}')
            self.sendMessage(orjson.dumps(
                response, option=orjson.OPT_APPEND_NEWLINE), isBinary)
        else:
            log.debug(f'{self.peer} updated bbox: {bbox}')
            self.bbox = bbox

    def onClose(self, wasClean, code, reason):
        log.debug(
            f"WebSocket connection closed by {self.forwarded_for} via {self.peer}: wasClean={wasClean} code={code} reason={reason}")
        self.run = False
        self.factory.feeder_factory.unregisterClient(self)


class WSServerFactory(WebSocketServerFactory):

    protocol = WSServerProtocol
    _subprotocols = ['sonde-geobuf', 'sonde-json']



class StateResource(Resource):

    def __init__(self, flight_observer, websocket_factory):
        self.observer = flight_observer
        self.websocket_factory = websocket_factory

    def render_GET(self, request):
        self.now = datetime.utcnow().timestamp()
        log.debug(f'render_GET request={request} args={request.args}')
        rates, distribution, observations, span = self.observer.stats()
        request.setHeader("Content-Type", "text/html; charset=utf-8")
        distribution_table = ""
        for k, v in distribution:
            distribution_table += f"\t\t<tr><td>{k}</td><td>{v}%</td></tr>\n"

        upstreams = """
<table>
<tr>
    <th>feed</th>
    <th>(re)connects)</th>
    <th>msgs received</th>
    <th>total byes</th>
    <th>typus</th>
</tr>"""
        for u in self.feeder_factory.upstreams:
            upstreams += (

#FIXME          self.feeder_factory.connects[host]['connects'] += 1
                f"<tr><td>{u.transport.getPeer()}</td>"
                f"<td>{u.feedstats['connects']}</td>"
                f"<td>{u.feedstats['lines']}</td>"
                f"<td>{u.feedstats['bytes']}</td>"
                f"<td>{u.factory.typus}</td>"
                f"</tr>\n"
            )
        upstreams += "</table>"

        tcp_clients = ""
        ws_clients = ""

        for client in self.feeder_factory.clients:
            if isinstance(client, Downstream):
                tcp_clients += f"\t\t<tr><td>{client.transport.getPeer()}</td><td>{client.bbox}</td></tr>\n"

            if isinstance(client, WSServerProtocol):
                ws_clients += (
                    f"\t\t<tr><td>{client.peer}</td>"
                    f"<td>{client.bbox}</td>"
                    f"<td>{client.usr}</td>"
                    f"<td>{client.forwarded_for}</td>"
                    f"<td>{client.user_agent}</td></tr>\n"
                    f"<td>{self.now - client.last_heard:.1f} s ago</td></tr>\n"
                    f"</tr>\n"
                )
        aircraft = """
<H2>Aircraft observed</H2>
<table>
<tr>
    <th>icao</th>
    <th>callsign</th>
    <th>sqawk</th>
    <th>lat</th>
    <th>lon</th>
    <th>altitude</th>
    <th>speed</th>
    <th>vspeed</th>
    <th>heading</th>
</tr>"""
        for icao, o in observations.items():
            #log.debug(f'icao={icao} o={o}')
            if not o.isPresentable():
                continue
            d = o.as_dict()
            aircraft += "<tr>"
            for k in ["icao24", "callsign", "squawk", "lat", "lon", "altitude", "speed", "vspeed", "heading"]:
                aircraft += f'<td>{d[k]}</td>'
            aircraft += "</tr>"
        aircraft += "</table>"

        response = f"""\
<HTML>
    <HEAD><TITLE>ADS-B feed statistics</title></head>
    <BODY>
    <H1>ADS-B feed statistics as of {datetime.today()}</H1>
    <H2>observation statistics (last {span} seconds)</H2>
    <table>
    <tr>
        <td>currently observing:</td>
        <td>{rates['observations']} aircraft</td>
    </tr>
    <tr>
        <td>observation rate:</td>
        <td>{rates['observation_rate']}/s</td>
    </tr>
    </table>
    <H2>SBS-1 Message type distribution</H2>
    <table>
       {distribution_table}
    </table>
    <H2>ADS-B feeders</H2>
   {upstreams}
    <H2>Websocket clients</H2>
    <table>
       {ws_clients}
    </table>
    <H2>TCP clients</H2>
    <table>
       {tcp_clients}
    </table>
    {aircraft}
    </body>
</html>"""
        return response.encode('utf-8')


def Bzip2Rotator(source, dest):
    with open(source, "rb") as sf:
        compressed = bz2.compress(sf.read(), 9)
        with open(f"{dest}.bz2", "wb") as df:
            df.write(compressed)
    os.remove(source)

def setup_logging(level, appName, logDir):
    global log
    log = logging.getLogger(appName)
    log.setLevel(level)

    logHandler = handlers.TimedRotatingFileHandler(f"{logDir}/{appName}.log",
                                                   when='midnight',
                                                   backupCount=7)
    logHandler.rotator = Bzip2Rotator
    fmt = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)-3s '
                            '%(filename)-12s%(lineno)3d %(message)s')

    if level == logging.DEBUG:
        stderrHandler = logging.StreamHandler(sys.stderr)
        stderrHandler.setLevel(level)
        stderrHandler.setFormatter(fmt)
        log.addHandler(stderrHandler)

    logHandler.setFormatter(fmt)
    logHandler.setLevel(level)
    log.addHandler(logHandler)

def doPrint(*args):
    log.info(f"0MQ message received: {args}")

def main():
    parser = argparse.ArgumentParser(
        description='serve radiosonde paths and updates via websockets',
        add_help=True)

    parser.add_argument('--method',
                        dest='method',
                        action='store',
                        type=str,
                        default='connect',
                        help='0MQ socket connection: bind|connect')

    parser.add_argument('--endpoint',
                        dest='endpoint',
                        action='store',
                        type=str,
                        default="tcp://86.59.12.250:9021",
                        help='0MQ Endpoint')

    parser.add_argument('--topic',
                        dest='topics',
                        action='append',
                        type=bytes,
                        default=[b'sondes'],
                        help='0MQ subscription topics')

    parser.add_argument('--websocket',
                        dest='websocket',
                        action='store',
                        type=str,
                        default=None,
                        help='websocket listen definition like ws://127.0.0.1:1080')

    parser.add_argument('-l', '--log',
                        help="set the logging level. Arguments:  DEBUG, INFO, WARNING, ERROR, CRITICAL",
                        choices=['DEBUG', 'INFO',
                                 'WARNING', 'ERROR', 'CRITICAL'],
                        dest="logLevel")

    parser.add_argument('--log-dir',
                        dest='logDir',
                        action='store',
                        default=defaultLogDir,
                        type=str,
                        help='directory to save logfiles in')

    parser.add_argument('--pub-socket',
                        dest='pubSocket',
                        action='store',
                        default=None,
                        type=str,
                        help='publishing socket like ipc:///tmp/adsb-json-feed or tcp://127.0.0.1:5001')

    parser.add_argument('--reporter',
                        dest='reporter',
                        action='store',
                        type=str,
                        default=None,
                        help='HTTP status report listen definition like tcp:1080')


    args = parser.parse_args()

    level = logging.WARNING
    if args.logLevel:
        level = getattr(logging, args.logLevel)

    setup_logging(level, appName, args.logDir)

    log.debug(f"{appName} starting up")
    boundingbox.log = log
    jwt_authenticator = JWTAuthenticator(issuer="urn:mah.priv.at",
                                         audience=WSServerFactory._subprotocols,
                                         algorithm="HS256")
    bbox_validator = boundingbox.BBoxValidator()
    websocket_factory = None

    if args.websocket:
        websocket_factory = WSServerFactory(args.websocket)
        websocket_factory.bbox_validator = bbox_validator
        websocket_factory.jwt_auth = jwt_authenticator

    flight_observer = None #observer.FlightObserver()

    if args.websocket:
        #websocket_factory.feeder_factory = feeder_factory
        listenWS(websocket_factory)

    if args.reporter:
        root = Resource()
        root.putChild(b"", StateResource(flight_observer, websocket_factory))
        webserver = serverFromString(reactor, args.reporter).listen(Site(root))


    zmqSocket = None
    if args.endpoint:
        zmqFactory = ZmqFactory()
        zmqEndpoint = ZmqEndpoint(args.method, args.endpoint)
        zmqSocket = ZmqSubConnection(zmqFactory, zmqEndpoint)
        for topic in args.topics:
            zmqSocket.subscribe(topic)
        zmqSocket.gotMessage = doPrint

    lc = LoopingCall(client_updater, flight_observer, zmqSocket)
    lc.start(0.3)

    setproctitle.setproctitle((f"{appName} "
                               f"logdir={args.logDir} "))
    reactor.run()


if __name__ == '__main__':
    main()