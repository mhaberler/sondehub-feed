#!/usr/bin/env python
import sys
import zmq
import geojson
import orjson
from datetime import time, datetime, date
import ciso8601

feedSocket = "ipc:///tmp/adsb-json-feed"
feedSocket = "tcp://86.59.12.250:9021"
topic = b'sondes'

# raw_decoded = "$$RS_R3320098,5251,18:02:45,49.64283,8.99417,20869,""
# "21.5,-67.3,3.2,RS41-SGP R3320098 402.700 MHz 41.1hPa 2.6V*EED4"
raob = {
    "type": "payload_telemetry",
    "data": {
        "_raw": "JCRSU19SMzMyMDA5OCw1MjUxLDE4OjAyOjQ1LDQ5LjY0MjgzLDguOTk0MTcsMjA4NjksMjEuNSwtNjcuMywzLjIsUlM0MS1TR1AgUjMzMjAwOTggNDAyLjcwMCBNSHogNDEuMWhQYSAyLjZWKkVFRDQK"},
    "receivers": {
        "DG8JT": {
            "time_created": "2021-01-19T18:02:30.092818Z",
            "time_uploaded": "2021-01-19T18:02:30.092818Z"
        }
    },
    "version": "autorx-1.4.0",
    "decoded": {
        "serial": "b\'$$RS_R3320098",
        "frame": "5251",
        "time": "18:02:45",
        "location": {
               "lat": "49.64283",
               "lon": "8.99417"
        },
        "alt": "20869",
        "vel_h": "21.5",
        "temp": "-67.3",
        "humidity": "3.2",
        "comment": "RS41-SGP R3320098 402.700 MHz 41.1hPa 2.6V",
        "checksum": "EED4\\\\n\'",
        "type": "payload_telemetry",
        "receiver": "DG8JT",
        "time_created": "2021-01-19T18:02:30.092818Z",
        "time_uploaded": "2021-01-19T18:02:30.092818Z"
    }
}
with_bt = {
    "type": "payload_telemetry",
    "data": {
        "_raw": "JCRSU19TMjI3MDQ5MSw4MTMxLDA2OjM1OjE1LDQ4LjE2MDc0LDEyLjI4NTcwLDExNzI0LDQ5LjksLTcxLjcsNDcuOSxSUzQxLVNHUCBTMjI3MDQ5MSA0MDQuNDk5IE1IeiAxOTQuOWhQYSBCVCAwODowNDoxNSAyLjVWKjlBNkYK"
    },
    "receivers": {
        "DL1JHR-15": {
            "time_created": "2021-01-19T06:35:00.115825Z",
            "time_uploaded": "2021-01-19T06:35:00.115825Z"
        }
    },
    "version": "autorx-1.4.0",
    "decoded": {
        "serial": "$$RS_S2270491",
        "frame": "8131",
        "time": "06:35:15",
        "location": {
            "lat": "48.16074",
            "lon": "12.28570"
        },
        "alt": "11724",
        "vel_h": "49.9",
        "temp": "-71.7",
        "humidity": "47.9",
        "comment": "RS41-SGP S2270491 404.499 MHz 194.9hPa BT 08:04:15 2.5V",
        "checksum": "9A6F'",
        "type": "payload_telemetry",
        "receiver": "DL1JHR-15",
        "time_created": "2021-01-19T06:35:00.115825Z",
        "time_uploaded": "2021-01-19T06:35:00.115825Z"
    }
}


xxx = '{"geometry": {"coordinates": [12.03185, 52.77216, 16416.0], "type": "Point"}, "properties": {"frequency": 405.701, "humidity": 10.4, "pressure": 87.0, "serial": "RS_R3320595", "temp": -72.7, "time": 1611123990.131321, "vel_h": 19.3, "voltage": 2.4}, "type": "Feature"}'


aircraft = dict()
count = 0

def process(msg):
    serial = msg.properties['serial']
    observed = msg.properties['time']

    if not serial in aircraft:
        fc = geojson.FeatureCollection([msg])
        fc['firstseen'] = observed
        fc['lastseen'] = observed
        aircraft[serial] = fc
        global count
        count += 1
        print(f'new {count}: {serial}')
    else:
        entry = aircraft[serial]
        entry['lastseen'] = observed
        entry.features.append(msg)
        print(f'add {count}: {serial} len={len(entry.features)}')

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





def main():
    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.connect(feedSocket)
    s.subscribe(topic)

    try:
        while True:
            t, msg = s.recv_multipart()
            #print(type(msg))
            js = orjson.loads(msg)
            gj = as_geojson(js)
            #print(js)
            #print(gj)
            process(gj)
    except KeyboardInterrupt:
        pass
    print("Done.")


if __name__ == "__main__":
    main()
