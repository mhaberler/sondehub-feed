all: messages_pb2.py geobuf_pb2.py node/messages.js

messages_pb2.py:	messages.proto
	protoc --proto_path=. --python_out=. messages.proto


geobuf_pb2.py:	geobuf.proto
		protoc --proto_path=. --python_out=. geobuf.proto


node/messages.js: messages.proto
		pbf  messages.proto > node/messages.js
