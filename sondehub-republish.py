# pip3 install boto3 paho-mqtt

# import hashlib
# import hmac
# import boto3
# import time
# import uuid
# import paho.mqtt.client as mqtt
# from urllib.parse import urlparse
# import urllib.parse
import sondehub
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
import json
import datetime

appName = "sondehub-republisher"
defaultLoglevel = 'INFO'
DEALER_IDENTITY = b'sondes'
minDelay = 3
maxDelay = 120
reconnectPause = 10


class SondeRepublisher(sondehub.Stream):

    def __init__(self,
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

        self.shstream = sondehub.Stream.__init__(self,
                                                 on_connect=self.on_connect,
                                                 on_message=self.on_message)

    def run(self, *args, **kwargs):
        log.debug(f"loop_forever")
        self.mqttc.loop_forever(**kwargs)

    def on_connect(self):
        log.info(f"on_connect")

    def on_message(self, msg):
        log.debug(f"on_message msg={msg}")
        m = json.dumps(msg, indent=4).encode("utf8")
        self.pubSocket.send_multipart([b'decoded',m])
        if self.dealerSocket:
            try:
                self.dealerSocket.send(m, zmq.DONTWAIT)
            except zmq.error.Again:
                pass

    def on_publish(self, mqttc, obj, mid):
        log.debug(f"on_publish mid={str(mid)}")

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        log.info(f"on_subscribe topic={str(mid)} granted_qos={granted_qos}")

    def on_log(self, mqttc, obj, level, string):
        log.log(level, f"on_log msg='{string}'")

    # def on_disconnect(self, client, userdata, rc):
    #     log.warn(f"Unexpected MQTT disconnection: userdata={userdata} reason={rc}, exit for restart")
    #     sys.exit(0) # let systemd do the restart
    #     # time.sleep(reconnectPause)
    #     # self.reconnect()

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


    args = parser.parse_args()
    setup_logging(getattr(logging, args.logLevel), appName, args.logDir)
    signal.signal(signal.SIGUSR1, usr1_handler)

    log.info(f"starting up")

    sp = SondeRepublisher(pubSocketURI=args.pubSocket,
                          dealerSocketURI=args.dealerSocket,
                          logger=log)

    setproctitle.setproctitle((f"{appName} log={log.getEffectiveLevel()} "
                               f"logdir={args.logDir} "))
    #sp.run(retry_first_connection=True, timeout=20.0)
    while 1:
        pass

if __name__ == '__main__':
    main()
