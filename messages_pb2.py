# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: messages.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import geobuf_pb2 as geobuf__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='messages.proto',
  package='airborne',
  syntax='proto2',
  serialized_options=b'H\003',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0emessages.proto\x12\x08\x61irborne\x1a\x0cgeobuf.proto\"+\n\tTimestamp\x12\x0f\n\x07seconds\x18\x01 \x02(\x03\x12\r\n\x05nanos\x18\x02 \x01(\x05\"\x84\x02\n\nMadisSonde\x12,\n\x0fsonde_validtime\x18\x01 \x02(\x0b\x32\x13.airborne.Timestamp\x12\'\n\nupdated_at\x18\x02 \x02(\x0b\x32\x13.airborne.Timestamp\x12\x0e\n\x06wmo_id\x18\x03 \x02(\t\x12\x14\n\x0ctemperatureK\x18\x04 \x03(\x02\x12\x11\n\tdewpointK\x18\x05 \x03(\x02\x12\x13\n\x0bpressurehPA\x18\x06 \x03(\x02\x12\x10\n\x08u_windMS\x18\x07 \x03(\x02\x12\x10\n\x08v_windMS\x18\x08 \x03(\x02\x12\x17\n\x08location\x18\t \x02(\x0b\x32\x05.Data\x12\x14\n\x0cstation_name\x18\n \x02(\t\"\xb9\x02\n\x0fServerContainer\x12*\n\x03typ\x18\x01 \x02(\x0e\x32\x1d.airborne.ServerContainerType\x12\x16\n\x0e\x63lient_message\x18\x02 \x01(\t\x12\x14\n\x0cseconds_left\x18\x03 \x01(\r\x12\x14\n\x0cmystery_data\x18\x04 \x03(\x0c\x12\x0e\n\x06topics\x18\x05 \x03(\t\x12\x1c\n\rsonde_updates\x18\n \x03(\x0b\x32\x05.Data\x12\x1a\n\x0bsonde_paths\x18\x0f \x03(\x0b\x32\x05.Data\x12\x1a\n\x0bmadis_paths\x18\x14 \x03(\x0b\x32\x05.Data\x12\x18\n\tdwd_paths\x18\x19 \x03(\x0b\x32\x05.Data\x12\x1b\n\x0c\x61\x64sb_updates\x18\x1e \x03(\x0b\x32\x05.Data\x12\x19\n\nadsb_paths\x18# \x03(\x0b\x32\x05.Data\"\x93\x01\n\x0b\x42oundingBox\x12\x14\n\x0cmin_latitude\x18\x01 \x02(\x02\x12\x14\n\x0cmax_latitude\x18\x02 \x02(\x02\x12\x15\n\rmin_longitude\x18\x03 \x02(\x02\x12\x15\n\rmax_longitude\x18\x04 \x02(\x02\x12\x14\n\x0cmin_altitude\x18\x05 \x01(\x02\x12\x14\n\x0cmax_altitude\x18\x06 \x01(\x02\"r\n\x0f\x43lientContainer\x12*\n\x03typ\x18\x01 \x02(\x0e\x32\x1d.airborne.ClientContainerType\x12#\n\x04\x62\x62ox\x18\x02 \x01(\x0b\x32\x15.airborne.BoundingBox\x12\x0e\n\x06topics\x18\x05 \x03(\t*H\n\x13ServerContainerType\x12\r\n\tMT_UPDATE\x10\x01\x12\x0b\n\x07MT_DUMP\x10\x03\x12\x15\n\x11MT_CLIENT_MESSAGE\x10\x04*;\n\x13\x43lientContainerType\x12\x12\n\x0eMT_UPDATE_BBOX\x10\x01\x12\x10\n\x0cMT_SUBSCRIBE\x10\x02\x42\x02H\x03'
  ,
  dependencies=[geobuf__pb2.DESCRIPTOR,])

_SERVERCONTAINERTYPE = _descriptor.EnumDescriptor(
  name='ServerContainerType',
  full_name='airborne.ServerContainerType',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='MT_UPDATE', index=0, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='MT_DUMP', index=1, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='MT_CLIENT_MESSAGE', index=2, number=4,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=932,
  serialized_end=1004,
)
_sym_db.RegisterEnumDescriptor(_SERVERCONTAINERTYPE)

ServerContainerType = enum_type_wrapper.EnumTypeWrapper(_SERVERCONTAINERTYPE)
_CLIENTCONTAINERTYPE = _descriptor.EnumDescriptor(
  name='ClientContainerType',
  full_name='airborne.ClientContainerType',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='MT_UPDATE_BBOX', index=0, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='MT_SUBSCRIBE', index=1, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1006,
  serialized_end=1065,
)
_sym_db.RegisterEnumDescriptor(_CLIENTCONTAINERTYPE)

ClientContainerType = enum_type_wrapper.EnumTypeWrapper(_CLIENTCONTAINERTYPE)
MT_UPDATE = 1
MT_DUMP = 3
MT_CLIENT_MESSAGE = 4
MT_UPDATE_BBOX = 1
MT_SUBSCRIBE = 2



_TIMESTAMP = _descriptor.Descriptor(
  name='Timestamp',
  full_name='airborne.Timestamp',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='seconds', full_name='airborne.Timestamp.seconds', index=0,
      number=1, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='nanos', full_name='airborne.Timestamp.nanos', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=42,
  serialized_end=85,
)


_MADISSONDE = _descriptor.Descriptor(
  name='MadisSonde',
  full_name='airborne.MadisSonde',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='sonde_validtime', full_name='airborne.MadisSonde.sonde_validtime', index=0,
      number=1, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='updated_at', full_name='airborne.MadisSonde.updated_at', index=1,
      number=2, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='wmo_id', full_name='airborne.MadisSonde.wmo_id', index=2,
      number=3, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='temperatureK', full_name='airborne.MadisSonde.temperatureK', index=3,
      number=4, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='dewpointK', full_name='airborne.MadisSonde.dewpointK', index=4,
      number=5, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='pressurehPA', full_name='airborne.MadisSonde.pressurehPA', index=5,
      number=6, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='u_windMS', full_name='airborne.MadisSonde.u_windMS', index=6,
      number=7, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='v_windMS', full_name='airborne.MadisSonde.v_windMS', index=7,
      number=8, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='location', full_name='airborne.MadisSonde.location', index=8,
      number=9, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='station_name', full_name='airborne.MadisSonde.station_name', index=9,
      number=10, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=88,
  serialized_end=348,
)


_SERVERCONTAINER = _descriptor.Descriptor(
  name='ServerContainer',
  full_name='airborne.ServerContainer',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='typ', full_name='airborne.ServerContainer.typ', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='client_message', full_name='airborne.ServerContainer.client_message', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='seconds_left', full_name='airborne.ServerContainer.seconds_left', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='mystery_data', full_name='airborne.ServerContainer.mystery_data', index=3,
      number=4, type=12, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='topics', full_name='airborne.ServerContainer.topics', index=4,
      number=5, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='sonde_updates', full_name='airborne.ServerContainer.sonde_updates', index=5,
      number=10, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='sonde_paths', full_name='airborne.ServerContainer.sonde_paths', index=6,
      number=15, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='madis_paths', full_name='airborne.ServerContainer.madis_paths', index=7,
      number=20, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='dwd_paths', full_name='airborne.ServerContainer.dwd_paths', index=8,
      number=25, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='adsb_updates', full_name='airborne.ServerContainer.adsb_updates', index=9,
      number=30, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='adsb_paths', full_name='airborne.ServerContainer.adsb_paths', index=10,
      number=35, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=351,
  serialized_end=664,
)


_BOUNDINGBOX = _descriptor.Descriptor(
  name='BoundingBox',
  full_name='airborne.BoundingBox',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='min_latitude', full_name='airborne.BoundingBox.min_latitude', index=0,
      number=1, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='max_latitude', full_name='airborne.BoundingBox.max_latitude', index=1,
      number=2, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='min_longitude', full_name='airborne.BoundingBox.min_longitude', index=2,
      number=3, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='max_longitude', full_name='airborne.BoundingBox.max_longitude', index=3,
      number=4, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='min_altitude', full_name='airborne.BoundingBox.min_altitude', index=4,
      number=5, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='max_altitude', full_name='airborne.BoundingBox.max_altitude', index=5,
      number=6, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=667,
  serialized_end=814,
)


_CLIENTCONTAINER = _descriptor.Descriptor(
  name='ClientContainer',
  full_name='airborne.ClientContainer',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='typ', full_name='airborne.ClientContainer.typ', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='bbox', full_name='airborne.ClientContainer.bbox', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='topics', full_name='airborne.ClientContainer.topics', index=2,
      number=5, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=816,
  serialized_end=930,
)

_MADISSONDE.fields_by_name['sonde_validtime'].message_type = _TIMESTAMP
_MADISSONDE.fields_by_name['updated_at'].message_type = _TIMESTAMP
_MADISSONDE.fields_by_name['location'].message_type = geobuf__pb2._DATA
_SERVERCONTAINER.fields_by_name['typ'].enum_type = _SERVERCONTAINERTYPE
_SERVERCONTAINER.fields_by_name['sonde_updates'].message_type = geobuf__pb2._DATA
_SERVERCONTAINER.fields_by_name['sonde_paths'].message_type = geobuf__pb2._DATA
_SERVERCONTAINER.fields_by_name['madis_paths'].message_type = geobuf__pb2._DATA
_SERVERCONTAINER.fields_by_name['dwd_paths'].message_type = geobuf__pb2._DATA
_SERVERCONTAINER.fields_by_name['adsb_updates'].message_type = geobuf__pb2._DATA
_SERVERCONTAINER.fields_by_name['adsb_paths'].message_type = geobuf__pb2._DATA
_CLIENTCONTAINER.fields_by_name['typ'].enum_type = _CLIENTCONTAINERTYPE
_CLIENTCONTAINER.fields_by_name['bbox'].message_type = _BOUNDINGBOX
DESCRIPTOR.message_types_by_name['Timestamp'] = _TIMESTAMP
DESCRIPTOR.message_types_by_name['MadisSonde'] = _MADISSONDE
DESCRIPTOR.message_types_by_name['ServerContainer'] = _SERVERCONTAINER
DESCRIPTOR.message_types_by_name['BoundingBox'] = _BOUNDINGBOX
DESCRIPTOR.message_types_by_name['ClientContainer'] = _CLIENTCONTAINER
DESCRIPTOR.enum_types_by_name['ServerContainerType'] = _SERVERCONTAINERTYPE
DESCRIPTOR.enum_types_by_name['ClientContainerType'] = _CLIENTCONTAINERTYPE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Timestamp = _reflection.GeneratedProtocolMessageType('Timestamp', (_message.Message,), {
  'DESCRIPTOR' : _TIMESTAMP,
  '__module__' : 'messages_pb2'
  # @@protoc_insertion_point(class_scope:airborne.Timestamp)
  })
_sym_db.RegisterMessage(Timestamp)

MadisSonde = _reflection.GeneratedProtocolMessageType('MadisSonde', (_message.Message,), {
  'DESCRIPTOR' : _MADISSONDE,
  '__module__' : 'messages_pb2'
  # @@protoc_insertion_point(class_scope:airborne.MadisSonde)
  })
_sym_db.RegisterMessage(MadisSonde)

ServerContainer = _reflection.GeneratedProtocolMessageType('ServerContainer', (_message.Message,), {
  'DESCRIPTOR' : _SERVERCONTAINER,
  '__module__' : 'messages_pb2'
  # @@protoc_insertion_point(class_scope:airborne.ServerContainer)
  })
_sym_db.RegisterMessage(ServerContainer)

BoundingBox = _reflection.GeneratedProtocolMessageType('BoundingBox', (_message.Message,), {
  'DESCRIPTOR' : _BOUNDINGBOX,
  '__module__' : 'messages_pb2'
  # @@protoc_insertion_point(class_scope:airborne.BoundingBox)
  })
_sym_db.RegisterMessage(BoundingBox)

ClientContainer = _reflection.GeneratedProtocolMessageType('ClientContainer', (_message.Message,), {
  'DESCRIPTOR' : _CLIENTCONTAINER,
  '__module__' : 'messages_pb2'
  # @@protoc_insertion_point(class_scope:airborne.ClientContainer)
  })
_sym_db.RegisterMessage(ClientContainer)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
