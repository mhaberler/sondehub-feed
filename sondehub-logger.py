#!/usr/bin/env python
import zmq
import logging
import logging.handlers as handlers
import argparse
import sys
import os
import bz2
import signal
import setproctitle

appName = "sondehub-logger"
defaultLoglevel = 'INFO'
subSocket = "ipc:///tmp/sondehub-feed"
topics = ["sondes"]

def sondeLogger(connect_to, topics):
    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.connect(connect_to)

    if not topics:
        s.subscribe("")
    else:
        for t in topics:
            s.subscribe(t)
    while True:
        topic, msg = s.recv_multipart()
        log.info(msg)

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
    parser = argparse.ArgumentParser(description='log sondehub feed via zmq',
                                     add_help=True)

    parser.add_argument('--sub-socket',
                        dest='subSocket',
                        action='store',
                        default=os.environ.get('LOGGER_SUBSOCKET', subSocket),
                        type=str,
                        help='listening socket like ipc:///tmp/sondehub-feed or tcp://127.0.0.1:5001')

    parser.add_argument('--topic',
                        dest='topics',
                        action='append',
                        type=str,
                        default=os.environ.get('LOGGER_TOPICS', topics),
                        help='topic to subscribe to. May be repeated.')

    parser.add_argument('--log-dir',
                        dest='logDir',
                        action='store',
                        default=os.environ.get('LOGGER_LOGDIR', '.'),
                        type=str,
                        help='directory to save logfiles in')

    parser.add_argument('-l', '--log',
                        help="set the logging level. Arguments:  DEBUG, INFO, WARNING, ERROR, CRITICAL",
                        default=os.environ.get('LOGGER_LOGLEVEL', defaultLoglevel),
                        choices=['DEBUG', 'INFO',
                                 'WARNING', 'ERROR', 'CRITICAL'],
                        dest="logLevel")

    args = parser.parse_args()
    setup_logging(getattr(logging, args.logLevel), appName, args.logDir)
    signal.signal(signal.SIGUSR1, usr1_handler)
    setproctitle.setproctitle((f"{appName} "
                               f"logdir={args.logDir} "
                               f"socket={args.subSocket} "
                               f"topics={args.topics}"))
    sondeLogger(args.subSocket, args.topics)

if __name__ == "__main__":
    main()
