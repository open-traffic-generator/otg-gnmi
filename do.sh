#!/bin/sh

OTG_API_VERSION=0.6.5
OPENCONFIG_GNMI_COMMIT=741cdaba27df2decde561afef843f16d0631373f
UT_REPORT=ut-report.html

# Avoid warnings for non-interactive apt-get install
export DEBIAN_FRONTEND=noninteractive

install_deps() {
	echo "Installing dependencies required by this project"
    apt-get update \
	&& apt-get -y install --no-install-recommends apt-utils dialog 2>&1 \
    && apt-get -y install python-is-python3 python3-pip \
    && python -m pip install --default-timeout=100 -r requirements.txt \
    && apt-get -y clean all
}

install_ext_deps() {
    echo "Installing extra dependencies required by this project"
    apt-get -y install curl vim git \
    && python -m pip install --default-timeout=100 flake8 requests pytest pytest-cov pytest_dependency pytest-html pytest-grpc pytest-asyncio asyncio mock coverage \
    && apt-get -y clean all
}

get_proto() {
    echo "Fetching proto files"
    rm -rf otg_gnmi/proto/> /dev/null 2>&1 || true \
    && mkdir otg_gnmi/proto/ \
    && get_otg_proto \
    && get_gnmi_proto

}

get_otg_proto() {
    echo "Fetching OTG proto for ${OTG_API_VERSION} ..."
    curl -kL https://github.com/open-traffic-generator/models/releases/download/v${OTG_API_VERSION}/otg.proto> ./otg_gnmi/proto/otg.proto
}

get_gnmi_proto() {
    echo "Fetching gNMI proto for ${OPENCONFIG_GNMI_COMMIT} ..."
    curl -kLO https://github.com/openconfig/gnmi/raw/${OPENCONFIG_GNMI_COMMIT}/proto/gnmi/gnmi.proto \
    && sed -i 's/github.com\/openconfig\/gnmi\/proto\/gnmi_ext\/gnmi_ext.proto/gnmi_ext.proto/g' ./gnmi.proto \
    && mv ./gnmi.proto ./otg_gnmi/proto \
    && curl -kLO https://github.com/openconfig/gnmi/raw/${OPENCONFIG_GNMI_COMMIT}/proto/gnmi_ext/gnmi_ext.proto \
    && mv ./gnmi_ext.proto ./otg_gnmi/proto
}

gen_py_stubs() {
    echo "Generating python stubs ..."
    rm -rf otg_gnmi/autogen/otg_*.py> /dev/null 2>&1 || true \
    && rm -rf otg_gnmi/autogen/gnmi_*.py> /dev/null 2>&1 || true
    curl -kLO https://github.com/open-traffic-generator/models/releases/download/v${OTG_API_VERSION}/protobuf3.tar.gz \
    && tar -xvf protobuf3.tar.gz \
    && sed -i 's/from protobuf3 import otg_pb2 as protobuf3_dot_otg__pb2/import otg_pb2 as otg__pb2/g' protobuf3/otg_pb2_grpc.py \
    && sed -i 's/protobuf3_dot_//g' protobuf3/otg_pb2_grpc.py \
    && cp ./protobuf3/otg_pb2_grpc.py ./otg_gnmi/autogen/otg_pb2_grpc.py \
    && cp ./protobuf3/otg_pb2.py ./otg_gnmi/autogen/otg_pb2.py \
    && rm -rf protobuf3.tar.gz protobuf3

    python -m grpc_tools.protoc --experimental_allow_proto3_optional -I./otg_gnmi/proto --python_out=./otg_gnmi/autogen --grpc_python_out=./otg_gnmi/autogen ./otg_gnmi/proto/gnmi.proto \
    && sed -i 's/import gnmi_pb2 as gnmi__pb2/from . import gnmi_pb2 as gnmi__pb2/g' ./otg_gnmi/autogen/gnmi_pb2_grpc.py \
    && sed -i 's/import gnmi_ext_pb2 as gnmi__ext__pb2/from . import gnmi_ext_pb2 as gnmi__ext__pb2/g' ./otg_gnmi/autogen/gnmi_pb2.py

    python -m grpc_tools.protoc --experimental_allow_proto3_optional -I./otg_gnmi/proto --python_out=./otg_gnmi/autogen --grpc_python_out=./otg_gnmi/autogen ./otg_gnmi/proto/gnmi_ext.proto
}

run() {
    echo "Running gNMI server ..."
    python -m otg_gnmi ${@}
}

run_unit_test() {
    echo "Running all unit tests ..."
    coverage run --source=./otg_gnmi -m pytest --html=${UT_REPORT} --self-contained-html ./tests/ 
    coverage report -m
    rm -rf ./otg_gnmi/__pycache__
    rm -rf ./tests/__pycache__
    rm -rf ./tests/.pytest_cache
    rm -rf ./tests/mockstatus.txt 2>&1 || true
    rm -rf ./tests/unit_api/__pycache__ 2>&1 || true
    rm -rf ./tests/unit_gnmi_clinet/__pycache__ 2>&1 || true
    rm .coverage
}

analyze_ut_result() {
    echo "Analyzing UT results..."
    ut_report=${UT_REPORT}
    total=$(cat ${ut_report} | grep -o -P '(?<=(<p>)).*(?=( tests))')
    echo "Number of Total Unit Tests: ${total}"
    passed=$(cat ${ut_report} | grep -o -P '(?<=(<span class="passed">)).*(?=( passed</span>))')
    echo "Number of Passed Unit Tests: ${passed}"
    if [ ${passed} = ${total} ]
    then 
        echo "All tests are passed..."
    else
        echo "All tests are not passed, Please check locally!"
        exit 1
    fi
    rm -rf ./${ut_report} 2>&1 || true
}

echo_version() {
    version=$(head ./version | cut -d' ' -f1)
    echo "gNMI version : ${version}"
}

build() {
    docker rmi -f "otg-gnmi-server"> /dev/null 2>&1 || true
    echo "Building production docker image..."
    docker build -t otg-gnmi-server .
    version=$(head ./version | cut -d' ' -f1)
    echo "gNMI - Server version : ${version}"
}

clean() {
    rm -rf logs
}

case $1 in
    deps  )
        install_deps
        ;;
    ext   )
        install_ext_deps
        ;;
    clean   )
        clean
        ;;
	run	    )
        # pass all args (except $1) to run
        shift 1
		run ${@}
		;;
	art	    )
		install_ext_deps && get_proto && gen_py_stubs && run_unit_test && analyze_ut_result
		;;
    unit    )
        run_unit_test
        ;;
    build    )
        build
        ;;
    version )
        echo_version
        ;;
	*   )
        $1 || echo "usage: $0 [deps|ext|clean|run|art|unit|build|version]"
		;;
esac
