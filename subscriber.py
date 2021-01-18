#!/usr/bin/env python
import sys
import zmq

subSocket = "ipc:///tmp/sondehub-feed"
topic = "sondes"
def main():
    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.connect(subSocket)
    s.subscribe(topic)
    try:
        while True:
            t, msg = s.recv_multipart()
            print('   Topic: %s, msg:%s' % (t, msg))
    except KeyboardInterrupt:
        pass
    print("Done.")


if __name__ == "__main__":
    main()
