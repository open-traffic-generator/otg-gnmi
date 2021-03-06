#!/bin/sh

OTG_API_VERSION=0.7.8
OPENCONFIG_GNMI_COMMIT=741cdaba27df2decde561afef843f16d0631373f

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
    && get_gnmi_proto

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
    rm -rf otg_gnmi/autogen/gnmi_*.py> /dev/null 2>&1 || true

    python -m grpc_tools.protoc --experimental_allow_proto3_optional -I./otg_gnmi/proto --python_out=./otg_gnmi/autogen --grpc_python_out=./otg_gnmi/autogen ./otg_gnmi/proto/gnmi.proto \
    && sed -i 's/import gnmi_pb2 as gnmi__pb2/from . import gnmi_pb2 as gnmi__pb2/g' ./otg_gnmi/autogen/gnmi_pb2_grpc.py \
    && sed -i 's/import gnmi_ext_pb2 as gnmi__ext__pb2/from . import gnmi_ext_pb2 as gnmi__ext__pb2/g' ./otg_gnmi/autogen/gnmi_pb2.py

    python -m grpc_tools.protoc --experimental_allow_proto3_optional -I./otg_gnmi/proto --python_out=./otg_gnmi/autogen --grpc_python_out=./otg_gnmi/autogen ./otg_gnmi/proto/gnmi_ext.proto
}

run() {
    echo "Running gNMI server ..."
    python -m otg_gnmi ${@}
}

run_test() {
    echo "Running all tests ..."
    run_clinet_test \
    && run_unit_test

}

run_unit_test() {
    echo "Running all api unit tests ..."
    REPORT="gnmi-api-ut.html"
    coverage run --source=./otg_gnmi -m pytest --html=${REPORT} --self-contained-html ./tests/unit_api
    analyze_result ${REPORT}
    rm -rf ./${REPORT} 2>&1 || true
    coverage report -m
    rm -rf ./otg_gnmi/__pycache__
    rm -rf ./tests/__pycache__
    rm -rf ./tests/.pytest_cache
    rm -rf ./tests/mockstatus.txt 2>&1 || true
    rm -rf ./tests/unit_api/__pycache__ 2>&1 || true
    rm -rf ./tests/unit_gnmi_clinet/__pycache__ 2>&1 || true
    rm .coverage
}

run_clinet_test() {
    echo "Running all gnmi client tests ..."
    REPORT="gnmi-client-ut.html"
    python -m pytest --html=${REPORT} --self-contained-html ./tests/unit_gnmi_clinet
    analyze_result ${REPORT}
    rm -rf ./${REPORT} 2>&1 || true
    rm -rf ./otg_gnmi/__pycache__
    rm -rf ./tests/__pycache__
    rm -rf ./tests/.pytest_cache
    rm -rf ./tests/mockstatus.txt 2>&1 || true
    rm -rf ./tests/unit_api/__pycache__ 2>&1 || true
    rm -rf ./tests/unit_gnmi_clinet/__pycache__ 2>&1 || true
}

analyze_result() {
    report=${1}
    echo "Analyzing results: ${report}"
    total=$(cat ${report} | grep -o -P '(?<=(<p>)).*(?=( tests))')
    echo "Number of Total Tests: ${total}"
    passed=$(cat ${report} | grep -o -P '(?<=(<span class="passed">)).*(?=( passed</span>))')
    echo "Number of Passed Tests: ${passed}"
    if [ ${passed} = ${total} ]
    then 
        echo "All tests are passed..."
    else
        echo "All tests are not passed, Please check locally!"
        exit 1
    fi
}

echo_version() {
    version=$(head ./version | cut -d' ' -f1)
    echo "gNMI version : ${version}"
}

build() {
    docker rmi -f "ixia-c-gnmi-server"> /dev/null 2>&1 || true
    echo "Building production docker image..."
    docker build -t ixia-c-gnmi-server .
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
		install_ext_deps && get_proto && gen_py_stubs && run_test
		;;
    unit    )
        run_test
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
