import orjson
import argparse
from datetime import datetime, timedelta, timezone, time, date
import base64
import geojson
import fileinput

#import geobuf
import ciso8601
import sys
import os
import logging
import logging.handlers as handlers

appName = "sonde2geojson"
defaultLoglevel = 'INFO'


def in_range(x, range):
    (lower, upper) = range
    if x < lower or x > upper:
        return False
    return True

# plausibility ranges
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


def as_geojson(js, timestring=False):
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
        d = ciso8601.parse_datetime(time_created)
    except ValueError:
        log.error(f"-- parse error {s} on '{time_created}'")
        properties["time"] = time_created
    else:
        if timestring:
            properties["time"] = d.isoformat()
        else:
            properties["time"] = d.timestamp()


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

def main():
    parser = argparse.ArgumentParser(description='convert sondehub json to geojson',
                                     add_help=True)
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    parser.add_argument('-l', '--log',
                        help="set the logging level. Arguments:  DEBUG, INFO, WARNING, ERROR, CRITICAL",
                        default=os.environ.get('LOGGER_LOGLEVEL', defaultLoglevel),
                        choices=['DEBUG', 'INFO',
                                 'WARNING', 'ERROR', 'CRITICAL'],
                        dest="logLevel")

    args = parser.parse_args()

    global log
    log = logging.getLogger(appName)
    stderrHandler = logging.StreamHandler(sys.stderr)
    stderrHandler.setLevel(getattr(logging, args.logLevel))
    fmt = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)-3s '
                            '%(filename)-12s:%(lineno)3d %(message)s')

    stderrHandler.setFormatter(fmt)
    log.addHandler(stderrHandler)

    for line in fileinput.input(files=args.files if len(args.files) > 0 else ('-', )):
        fields = line.strip().split(' ',5)
        js = orjson.loads(eval(fields[5]))
        print(orjson.dumps(as_geojson(js, timestring=True)).decode("utf8"))


if __name__ == "__main__":
    main()
