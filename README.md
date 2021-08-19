# OTG gNMI

gNMI interface to get stats from Ixia-C traffic generator

## Build

Gitlab is not reachable from within lab network, hence please make sure that the intended system is outside lab network (for build to succeed).


- **Clone this project**

  ```sh
  git clone --recursive https://github.com/open-traffic-generator/otg-gnmi.git
  cd otg-gnmi/
  ```

- **For Production**

    ```sh
    # this stage will create an intermediate, untagged image; feel free to get rid of it afterwards
    docker build -t otg-gnmi-server .
    # start container
    docker run -d --net=host otg-gnmi-server --app-mode ixia-c --target-host localhost --target-port 443
    # [checkout more options]
    docker run -d --net=host otg-gnmi-server help
    ```

- **For Development**

    ```sh
    # the project uses multi-stage build (defined in same Dockerfile) for both
    # dev and prod environment;
    # hence, to build dev image, you need to explicitly specify target `stage`
    docker build --target=dev -t otg-gnmi-server:dev .
    # Start container and you'll be placed inside the project dir
    docker run -it --net=host otg-gnmi-server:dev
    # [checkout more options]
    docker run -d --net=host otg-gnmi-server:dev help
    ```

- **(Optional) Setup VSCode**

    After development container is ready,
    - Install Remote Explorer Extension in VSCode
    - Restart VSCode and choose `Containers` dropdown in `Remote Explorer`
    - (Optional) If your container is on a remote machine, setup a password-less SSH against it and put following line inside VSCode settings:
      ```json
      "docker.host": "ssh://username@hostname"
      ```
    - If you see the intended container listed, attach to it and change working directory to `/home/keysight/ixia-c/otg-gnmi`
    - Allow it to install extensions and other tools when prompted


## Quick Tour

**do.sh** covers most of what needs to be done manually. If you wish to extend it, just define a function (e.g. install_deps()) and call it like so: `./do.sh install_deps`.

```sh
# start otg gnmi server
./do.sh run
# run unit / benchmark / coverage tests against all packages
./do.sh unit
# get unit test deps, generate stubs, run tests
./do.sh art
# build otg gnmi server docker image
./do.sh build
```
