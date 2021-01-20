all: protobuf/messages_pb2.py protobuf/geobuf_pb2.py

protobuf/messages_pb2.py:	protobuf/messages.proto
	protoc --proto_path=. --python_out=. protobuf/messages.proto


protobuf/geobuf_pb2.py:	protobuf/geobuf.proto
		protoc --proto_path=. --python_out=. protobuf/geobuf.proto
