#!/bin/bash

OTG_VERSION=0.4.12
mkdir tmp
cd tmp

# copy proto file
wget https://github.com/open-traffic-generator/models/releases/download/v$OTG_VERSION/otg.proto
cp ./otg.proto ../otg_gnmi/proto/otg.proto

# copy ./py files
wget https://github.com/open-traffic-generator/models/releases/download/v$OTG_VERSION/protobuf3.tar.gz
tar -xvf protobuf3.tar.gz
sed -i 's/from protobuf3 import otg_pb2 as protobuf3_dot_otg__pb2/import otg_pb2 as otg__pb2/g' protobuf3/otg_pb2_grpc.py
sed -i 's/protobuf3_dot_//g' protobuf3/otg_pb2_grpc.py

cp ./protobuf3/otg_pb2_grpc.py ../otg_gnmi/autogen/otg_pb2_grpc.py
cp ./protobuf3/otg_pb2.py ../otg_gnmi/autogen/otg_pb2.py
cd ..
rm -rf tmp


