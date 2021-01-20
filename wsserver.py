
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory, Protocol, Factory
from twisted.protocols import basic
from twisted.internet.endpoints import clientFromString, serverFromString
from twisted.internet.task import LoopingCall
from twisted.application.internet import ClientService, backoffPolicy, StreamServerEndpointService
from twisted.application import internet, service
#from twisted.python.log import PythonLoggingObserver, ILogObserver, startLogging, startLoggingWithObserver, addObserver
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.logger import Logger, LogLevel, LogLevelFilterPredicate, \
    textFileLogObserver, FilteringLogObserver, globalLogBeginner

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
from datetime import datetime, timedelta, timezone, time, date
import base64
from collections import Counter
import geojson

#import geobuf
import ciso8601
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPubConnection, ZmqSubConnection

import boundingbox
from jwt import InvalidAudienceError, ExpiredSignatureError, InvalidSignatureError, PyJWTError
from jwtauth import *

from google.protobuf.json_format import MessageToJson
import protobuf.messages_pb2 as messages
import protobuf.geobuf_pb2 as geo
from  protobuf.encode import Encoder
from  protobuf.decode import Decoder

#import geobuf

# from protobuf.geobuf_pb2 import Data
# import protobuf.messages_pb2
# from protobuf.geobuf_pb2 import Data
#
# from protobuf.messages_pb2 import ServerContainerType, ClientContainerType, Timestamp, \
#     MadisSonde, ServerContainer, BoundingBox, ClientContainer
appName = "sonde-server"
defaultLoglevel = 'INFO'
defaultLogDir = "/var/log/sonde-server"
defaultLogDir = "/tmp"
facility = syslog.LOG_LOCAL1
pubSocket = "ipc:///tmp/adsb-json-feed"

PING_EVERY = 30  # secs for now


def geobuf_encode(*args):
    return Encoder().encode(*args)


def geobuf_decode(*args):
    return Decoder().decode(*args)


def in_range(x, range):
    (lower, upper) = range
    if x < lower or x > upper:
        return False
    return True


valid_freq = (300, 1800)
valid_pressure = (0, 1200)
valid_temp = (-200, 100)
valid_humidity = (0, 100)
valid_ttl = (-3600, 36000)
valid_voltage = (1.8, 24)
valid_vel_h = (0.0001, 200)


def parse_comment(c, sonde_time):
    r = dict()
    fields = c.split()
    for i in range(len(fields)):
        f = fields[i]
        l = f.lower()
        if l == 'mhz':
            f = float(fields[i - 1])
            if in_range(f, valid_freq):
                r['frequency'] = f
        if sonde_time and l == 'bt':
            st = time.fromisoformat(sonde_time)
            bt = time.fromisoformat(fields[i + 1])
            ttl = datetime.combine(date.today(), bt) - \
                datetime.combine(date.today(), st)
            secs_left = ttl.total_seconds()
            if in_range(secs_left, valid_ttl):
                r['ttl'] = secs_left
        if l.endswith('hpa'):
            p = float(l[:-3])
            if in_range(p, valid_pressure):
                r['pressure'] = p
        if l.endswith('v'):
            v = float(l[:-1])
            if in_range(v, valid_voltage):
                r['voltage'] = v
    return r


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def as_geojson(js):
    decoded = js['decoded']
    sonde_time = decoded.get('time', None)
    comment_values = parse_comment(decoded['comment'], sonde_time)
    pos = decoded['location']

    point = geojson.Point((float(pos['lon']),
                           float(pos['lat']),
                           float(decoded['alt'])))
    properties = dict()
    properties["serial"] = remove_prefix(decoded['serial'], "b'$$")

    time_created = decoded['time_created']
    try:
        d = ciso8601.parse_datetime(time_created).timestamp()
    except ValueError:
        print(f"-- parse error {s}")
        d = time_created

    properties["time"] = d
    vel_h = float(decoded['vel_h'])
    if in_range(vel_h, valid_vel_h):
        properties['vel_h'] = vel_h

    humidity = float(decoded['humidity'])
    if in_range(humidity, valid_humidity):
        properties['humidity'] = humidity
    temp = float(decoded['temp'])
    if in_range(temp, valid_temp):
        properties['temp'] = temp

    feature = geojson.Feature(geometry=point,
                              properties={**comment_values, **properties})
    return feature


class SondeObservation(object):
    def __init__(self, name, when):
        self.featureCollection = geojson.FeatureCollection([])
        self.firstSeen = when
        self.name = name
        self.updated = False
        self.path_as_pbf = None

    def addSample(self, sample, when):
        self.lastSeen = when
        self.featureCollection.features.append(sample)
        self.updated = True
        self.last_sample_as_pbf = geobuf_encode(sample)

    def getPbfSample(self):
        return self.last_sample_as_pbf

    def getPbfPath(self):
        return geobuf_encode(self.__geo_interface__)

    def sampleCount(self):
        return len(self.featureCollection.features)

    @property
    def __geo_interface__(self):
        return self.featureCollection


class SondeObserver(object):
    def __init__(self):
        self.aircraft = dict()

    def getChanged(self):
        changed = []
        for k, v in self.aircraft.items():
            if v.updated:
                changed.append(v)
                v.updated = False
        return changed

    def processMessage(self, data, topic):
        log.debug(f"processMessage topic={topic} data={data}")
        js = orjson.loads(data)
        msg = as_geojson(js)
        serial = msg.properties['serial']
        observed = msg.properties['time']

        if not serial in self.aircraft:
            so = SondeObservation(serial, observed)
            self.aircraft[serial] = so
        so = self.aircraft[serial]
        so.addSample(msg, observed)
        log.debug((f"update sonde: {serial} samples={so.sampleCount()}"
                   f" loc={msg.geometry.coordinates}"))

    @property
    def __geo_interface__(self):
        fc = geojson.FeatureCollection([])
        for k, v in self.aircraft.items():
            fc.features.append(v)
        return fc



class WSServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        super().__init__()
        self.forwarded_for = ''
        logging.debug(f"WebSocket __init__")

    def onConnecting(self, transport_details):
        logging.info(f"WebSocket connecting: {transport_details}")
        self.last_heard = datetime.utcnow().timestamp()

    def doPing(self):
        if self.run:
            self.sendPing()
            reactor.callLater(PING_EVERY, self.doPing)

    def onPong(self, payload):
        self.last_heard = datetime.utcnow().timestamp()

    def onConnect(self, request):
        log.debug(
            f"Client connecting: {request.peer} version {request.version}")
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

        self.user_agent = request.headers.get('user-agent', "")

        log.debug(
            f"chosen protocol {self.proto} for {self.forwarded_for} via {self.peer} ua={self.user_agent}")

        # FIXME
        return self.proto

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
            log.info(
                f"no token passed in URI by {self.forwarded_for} via {request.peer}")
            raise ConnectionDeny(1066)

        # accept the WebSocket connection, speaking subprotocol `proto`
        # and setting HTTP headers `headers`
        # return (proto, headers)
        return self.proto

    def sessionExpired(self):
        self.factory.unregisterClient(self)
        log.debug(
            f"token validity time exceeded, closing {self.forwarded_for} via {self.peer}")
        self.sendClose()

    def onOpen(self):
        log.debug(f"connection open to {self.forwarded_for} via {self.peer}")
        self.run = True
        self.factory.registerClient(self)
        self.doPing()

        sc = messages.ServerContainer()
        sc.typ = messages.ServerContainerType.MT_DUMP
        # a full dump - FIXME needs bbox
        for k, v in self.factory.observer.aircraft.items():
            d = sc.sonde_paths.add()
            d.MergeFromString(v.getPbfPath())

        pbf = sc.SerializeToString()
        js = MessageToJson(sc,  use_integers_for_enums=True).encode()
        for client in self.factory.clients:
            if client.proto == 'sonde-geobuf':
                client.sendMessage(pbf, True)
            if client.proto == 'sonde-json':
                client.sendMessage(js, False)

    def onMessage(self, payload, isBinary):
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
        self.factory.unregisterClient(self)

    def notifyClient(self, msg):
        WebSocketProtocol.sendMessage(self, msg)


class WSServerFactory(WebSocketServerFactory):

    protocol = WSServerProtocol
    _subprotocols = ['sonde-geobuf', 'sonde-json']

    def __init__(self, url='ws://localhost',
                 observer=None,
                 bbox_validator=None,
                 jwt_authenticator=None):

        self.bbox_validator = bbox_validator
        self.jwt_authenticator = jwt_authenticator
        self.observer = observer
        self.clients = set()
        WebSocketServerFactory.__init__(self, url)
        log.debug(f"Listening on: {url}")

    def registerClient(self, client):
        self.clients.add(client)

    def unregisterClient(self, client):
        self.clients.discard(client)

    def notifyClients(self, message):
        log.debug(f"Broadcasting: {message}")
        for c in self.clients:
            c.notifyClient(message)
        log.debug(f"Sent messages")


    def updateClients(self):
        changed = self.observer.getChanged()
        if not changed:
            return
        sc = messages.ServerContainer()
        sc.typ = messages.ServerContainerType.MT_UPDATE
        for v in changed:
            d = sc.sonde_updates.add()
            d.MergeFromString(v.getPbfSample())

        pbf = sc.SerializeToString()
        js = MessageToJson(sc,  use_integers_for_enums=True).encode()
        for client in self.clients:
            if client.proto == 'sonde-geobuf':
                client.sendMessage(pbf, True)
            if client.proto == 'sonde-json':
                client.sendMessage(js, False)

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
        for u in self.upstreams:
            upstreams += (

                # FIXME          self.connects[host]['connects'] += 1
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

        for client in self.clients:
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

    logtargets = []
    logtargets.append(
        FilteringLogObserver(
            textFileLogObserver(sys.stderr),
            predicates=[LogLevelFilterPredicate(LogLevel.debug)]
        )
    )
    globalLogBeginner.beginLoggingTo(logtargets)


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

    observer = SondeObserver()

    if args.websocket:
        websocket_factory = WSServerFactory(url=args.websocket,
                                            observer=observer,
                                            bbox_validator=bbox_validator,
                                            jwt_authenticator=jwt_authenticator)
    flight_observer = None  # observer.FlightObserver()

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
        zmqSocket.gotMessage = observer.processMessage
        for topic in args.topics:
            zmqSocket.subscribe(topic)

    lc = LoopingCall(websocket_factory.updateClients)
    lc.start(0.5)

    setproctitle.setproctitle((f"{appName} "
                               f"logdir={args.logDir} "))
    reactor.run()


if __name__ == '__main__':
    main()
