# Python - gNMI docker image

FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
	&& apt-get -y install --no-install-recommends python3-pip 

WORKDIR /home/otg-gnmi

#COPY ./requirements.txt ./requirements.txt
#COPY ./otg-gnmi/proto/* ./otg-gnmi/proto/
#COPY ./otg-gnmi/autogen/*.py ./otg-gnmi/autogen/
#COPY ./otg-gnmi/common/*.py ./otg-gnmi/common/
#COPY ./otg-gnmi/test/*.py ./otg-gnmi/test/
#COPY ./otg-gnmi/*.py ./otg-gnmi/

COPY . /home/otg-gnmi/

RUN python3 -m pip install --upgrade -r requirements.txt

ENTRYPOINT [ "python3", "-m", "otg_gnmi" ]

# default server port
EXPOSE 50051

# sudo docker build -t otg-gnmi-server:latest .
# sudo docker run -p 50051:50051 --rm --name otg-gnmi-server-instance otg-gnmi-server:latest \
#		--server-port 50051 --app-mode ixnetwork \
#  		--target-host 10.72.46.133 --target-port 443 \
#		--server-key server.key --server-crt server.crt
# sudo docker exec -it otg-gnmi-server-instance sh

