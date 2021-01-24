# pip3 install boto3 paho-mqtt

import hashlib
import datetime
import hmac
import boto3
import time
import uuid
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
import urllib.parse
import zmq
import logging
import logging.handlers as handlers
import argparse
import syslog
import sys
import os
import bz2
import signal
import setproctitle
import geojson

appName = "sondehub-republisher"
defaultLoglevel = 'INFO'
DEALER_IDENTITY = b'sondes'
minDelay = 3
maxDelay = 120
reconnectPause = 10

def aws_sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def aws_getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = aws_sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = aws_sign(kDate, regionName)
    kService = aws_sign(kRegion, serviceName)
    kSigning = aws_sign(kService, 'aws4_request')
    return kSigning


def aws_presign(access_key=None, secret_key=None, session_token=None, host=None, region=None, method=None, protocol=None, uri=None, service=None, expires=3600, payload_hash=None):
    # method=GET, protocol=wss, uri=/mqtt service=iotdevicegateway
    assert 604800 >= expires >= 1, "Invalid expire time 604800 >= %s >= 1" % expires

    # Date stuff, first is datetime, second is just date.
    t = datetime.datetime.utcnow()
    date_time = t.strftime('%Y%m%dT%H%M%SZ')
    date = t.strftime('%Y%m%d')
    # Signing algorithm used
    algorithm = 'AWS4-HMAC-SHA256'

    # Scope of credentials, date + region (eu-west-1) + service (iot gateway hostname) + signature version
    credential_scope = date + '/' + region + '/' + service + '/' + 'aws4_request'
    # Start building the query-string
    canonical_querystring = 'X-Amz-Algorithm=' + algorithm
    canonical_querystring += '&X-Amz-Credential=' + \
        urllib.parse.quote_plus(access_key + '/' + credential_scope)
    canonical_querystring += '&X-Amz-Date=' + date_time
    canonical_querystring += '&X-Amz-Expires=' + str(expires)
    canonical_querystring += '&X-Amz-SignedHeaders=host'

    if payload_hash is None:
        if service == 'iotdevicegateway':
            payload_hash = hashlib.sha256(b'').hexdigest()
        else:
            payload_hash = 'UNSIGNED-PAYLOAD'

    canonical_headers = 'host:' + host + '\n'
    canonical_request = method + '\n' + uri + '\n' + canonical_querystring + \
        '\n' + canonical_headers + '\nhost\n' + payload_hash

    string_to_sign = algorithm + '\n' + date_time + '\n' + credential_scope + \
        '\n' + hashlib.sha256(canonical_request.encode()).hexdigest()
    signing_key = aws_getSignatureKey(secret_key, date, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode(
        'utf-8'), hashlib.sha256).hexdigest()

    canonical_querystring += '&X-Amz-Signature=' + signature
    if session_token:
        canonical_querystring += '&X-Amz-Security-Token=' + \
            urllib.parse.quote(session_token)

    return protocol + '://' + host + uri + '?' + canonical_querystring


class SondeRepublisher(mqtt.Client):

    def __init__(self,
                 clientId=str(uuid.uuid4()),
                 pubSocketURI=None,
                 dealerSocketURI=None,
                 logger=None,
                 clean_session=True):

        self.context = zmq.Context()

        self.pubSocket = self.context.socket(zmq.PUB)
        self.pubSocket.bind(pubSocketURI)

        if dealerSocketURI:
            self.dealerSocket = self.context.socket(zmq.DEALER)
            self.dealerSocket.bind(dealerSocketURI)
            self.dealerSocket.setsockopt(zmq.IDENTITY, DEALER_IDENTITY)

        else:
            self.dealerSocket = None

        mqtt.Client.__init__(self, client_id=clientId,
                             clean_session=clean_session, transport="websockets")
        self.enable_logger(logger=logger)
        log.debug(f"client_id={clientId} clean_session={clean_session}")

    def do_connect(self,
                   topic="sondes",
                   urlparts=None,
                   headers=None,
                   port=443,
                   keepalive=60):
        self.topic = topic
        self.ws_set_options(
            path=f"{urlparts.path}?{urlparts.query}", headers=headers)
        self.tls_set()
        self.reconnect_delay_set(min_delay=minDelay, max_delay=maxDelay)
        self.connect(urlparts.netloc, port, keepalive)

    def run(self, *args, **kwargs):
        log.debug(f"loop_forever")
        self.loop_forever(**kwargs)

    def on_connect(self, mqttc, obj, flags, rc):
        log.info(f"on_connect rc={rc}")
        self.subscribe(self.topic, 1)

    def on_message(self, mqttc, obj, msg):
        log.debug(
            f"on_message topic={msg.topic} qos={msg.qos} payload={str(msg.payload)}")
        self.pubSocket.send_multipart([msg.topic.encode(), msg.payload])
        if self.dealerSocket:
            try:
                self.dealerSocket.send(msg.payload, zmq.DONTWAIT)
            except zmq.error.Again:
                pass

    def on_publish(self, mqttc, obj, mid):
        log.debug(f"on_publish mid={str(mid)}")

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        log.info(f"on_subscribe topic={str(mid)} granted_qos={granted_qos}")

    def on_log(self, mqttc, obj, level, string):
        log.log(level, f"on_log msg='{string}'")

    # def on_disconnect(self, client, userdata, rc):
    #     log.warn(f"Unexpected MQTT disconnection, reconnecting after {reconnectPause}s. reason={rc}")
    #     time.sleep(reconnectPause)
    #     self.reconnect()

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def usr1_handler(signum, frame):
    """
    toggle between debug and default logging
    """
    currentLevel = log.getEffectiveLevel()
    if currentLevel == logging.DEBUG:
        currentLevel = getattr(logging, defaultLoglevel)
    else:
        currentLevel = logging.DEBUG
    log.setLevel(currentLevel)
    for handler in log.handlers:
        handler.setLevel(currentLevel)
    log.info(f"received signal {signum}, new loglevel={currentLevel}")


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
                                                   backupCount=14)
    logHandler.rotator = Bzip2Rotator
    fmt = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)-3s '
                            '%(filename)-12s:%(lineno)3d %(message)s')

    if level == logging.DEBUG:
        stderrHandler = logging.StreamHandler(sys.stderr)
        stderrHandler.setLevel(level)
        stderrHandler.setFormatter(fmt)
        log.addHandler(stderrHandler)

    logHandler.setFormatter(fmt)
    logHandler.setLevel(level)
    log.addHandler(logHandler)


def main():
    parser = argparse.ArgumentParser(
        description='receive sondehub feed and republish via zmq',
        add_help=True)

    parser.add_argument('--sondehub-host',
                        dest='sondehubHost',
                        action='store',
                        default=os.environ.get('SONDEHUB_HOST'),
                        type=str,
                        help='host to connect to')

    parser.add_argument('--sondehub-pool-id',
                        dest='sondehubPoolId',
                        action='store',
                        default=os.environ.get('SONDEHUB_POOLID'),
                        type=str,
                        help='sondehub identity pool id')

    parser.add_argument('--sondehub-region',
                        dest='sondehubRegion',
                        action='store',
                        default=os.environ.get('SONDEHUB_REGION'),
                        type=str,
                        help='AWS region')

    parser.add_argument('--client-id',
                        dest='clientId',
                        action='store',
                        default=os.environ.get('SONDEHUB_CLIENTID'),
                        type=str,
                        help='republishing socket like ipc:///tmp/sondehub-feed or tcp://127.0.0.1:5001')

    parser.add_argument('--pub-socket',
                        dest='pubSocket',
                        action='store',
                        default=os.environ.get('SONDEHUB_PUBSOCKET'),
                        type=str,
                        help='republishing socket like ipc:///tmp/sondehub-feed or tcp://127.0.0.1:5001')

    parser.add_argument('--dealer-socket',
                        dest='dealerSocket',
                        action='store',
                        default=os.environ.get('SONDEHUB_DEALERSOCKET'),
                        type=str,
                        help='republishing dealer socket like ipc:///tmp/sondehub-feed or tcp://127.0.0.1:5001')

    parser.add_argument('--log-dir',
                        dest='logDir',
                        action='store',
                        default=os.environ.get('SONDEHUB_LOGDIR', '.'),
                        type=str,
                        help='directory to save logfiles in')

    parser.add_argument('-l', '--log',
                        help="set the logging level. Arguments:  DEBUG, INFO, WARNING, ERROR, CRITICAL",
                        default=os.environ.get(
                            'SONDEHUB_LOGLEVEL', defaultLoglevel),
                        choices=['DEBUG', 'INFO',
                                 'WARNING', 'ERROR', 'CRITICAL'],
                        dest="logLevel")

    parser.add_argument("--persistent", type=str2bool, nargs='?',
                        default=os.environ.get('SONDEHUB_PERSISTENT', True),
                        const=False, dest='clean_session',
                        help="tell broker to keep queued messages (clean_session=False)")

    args = parser.parse_args()
    setup_logging(getattr(logging, args.logLevel), appName, args.logDir)
    signal.signal(signal.SIGUSR1, usr1_handler)

    log.info(f"starting up")

    identityPoolID = f"{args.sondehubRegion}:{args.sondehubPoolId}"
    cognitoIdentityClient = boto3.client(
        'cognito-identity', region_name=args.sondehubRegion)
    temporaryIdentityId = cognitoIdentityClient.get_id(
        IdentityPoolId=identityPoolID)
    identityID = temporaryIdentityId["IdentityId"]

    temporaryCredentials = cognitoIdentityClient.get_credentials_for_identity(
        IdentityId=identityID)
    AccessKeyId = temporaryCredentials["Credentials"]["AccessKeyId"]
    SecretKey = temporaryCredentials["Credentials"]["SecretKey"]
    SessionToken = temporaryCredentials["Credentials"]["SessionToken"]

    url = aws_presign(access_key=AccessKeyId,
                      secret_key=SecretKey,
                      session_token=SessionToken,
                      method="GET",
                      protocol="wss",
                      uri="/mqtt",
                      service="iotdevicegateway",
                      host=args.sondehubHost,
                      region=args.sondehubRegion)
    urlparts = urlparse(url)
    headers = {
        "Host": "{0:s}".format(urlparts.netloc),
    }
    sp = SondeRepublisher(pubSocketURI=args.pubSocket,
                          dealerSocketURI=args.dealerSocket,
                          logger=log,
                          clean_session=args.clean_session,
                          clientId=args.clientId)
    sp.do_connect(urlparts=urlparts, headers=headers)
    setproctitle.setproctitle((f"{appName} log={log.getEffectiveLevel()} "
                               f"logdir={args.logDir} "
                               f"host={args.sondehubHost}"))
    sp.run(retry_first_connection=True, timeout=20.0)


if __name__ == '__main__':
    main()
