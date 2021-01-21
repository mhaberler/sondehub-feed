
from datetime import datetime
from geojson import Feature, Point, FeatureCollection
from google.protobuf.json_format import MessageToJson, MessageToDict

import messages_pb2 as messages
#import geobuf_pb2 as geo

from  encode import Encoder
from  decode import Decoder


def geobuf_encode(*args):
    return Encoder().encode(*args)

def geobuf_decode(*args):
    return Decoder().decode(*args)


sc = messages.ServerContainer()
sc.typ = messages.ServerContainerType.MT_UPDATE
sc.client_message = "Hi there!"

sc.topics.append("foo")
sc.topics.append("bar")

#d = geo.Data()
# incremental update from already serialized protobuf
f =  Feature(geometry=Point((-80.234, -22.532)))
pbf = geobuf_encode(f)

d = sc.sonde_updates.add()
d.MergeFromString(pbf)


jsonObj = MessageToJson(sc,
                        use_integers_for_enums=True,
                        preserving_proto_field_name=True)
print(jsonObj)


print(sc)



pb = sc.SerializeToString()
print(pb)

sc2 = messages.ServerContainer()
sc2.ParseFromString(pb)

jsonObj = MessageToJson(sc2,  preserving_proto_field_name=True)
print(jsonObj)

dictionary = MessageToDict(sc2)
print(dictionary)




bbox = messages.BoundingBox()
bbox.min_latitude = 45.0
bbox.max_latitude = 48.0
bbox.min_longitude = 10.0
bbox.max_longitude = 16.0

cc = messages.ClientContainer()
cc.typ = messages.ClientContainerType.MT_UPDATE_BBOX
cc.bbox.MergeFrom(bbox)
# or cc.bbox.min_latitude = val

cc.topics.append("sondes")
cc.topics.append("sondes-paths")
cc.topics.append("madis")
cc.topics.append("dwd-paths")
cc.topics.append("adsb")
cc.topics.append("adsb-paths")

print(cc)

ts = messages.Timestamp()
ts.seconds = int(datetime.utcnow().timestamp())


fail = b'khgfsdkjhfgjdhsagflsadghflsdajhgfsaezezfajhsdglhdajs'
sc2 = messages.ServerContainer()
sc2.ParseFromString(fail)
