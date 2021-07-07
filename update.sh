#!/bin/bash

OTG_VERSION=v0.4.0
mkdir tmp
cd tmp
wget https://github.com/open-traffic-generator/models/releases/download/$OTG_VERSION/protobuf3.tar.gz
tar -xvf protobuf3.tar.gz
sed -i 's/from protobuf3 import otg_pb2 as protobuf3_dot_otg__pb2/import otg_pb2 as otg__pb2/g' protobuf3/otg_pb2_grpc.py
sed -i 's/protobuf3_dot_//g' protobuf3/otg_pb2_grpc.py
#sed -i 's/protobuf3.//g' protobuf3/otg_pb2.py

cp ./protobuf3/otg.proto ../otg_gnmi/proto/otg.proto
cp ./protobuf3/otg_pb2_grpc.py ../otg_gnmi/autogen/otg_pb2_grpc.py
cp ./protobuf3/otg_pb2.py ../otg_gnmi/autogen/otg_pb2.py
cd ..
rm -rf tmp

