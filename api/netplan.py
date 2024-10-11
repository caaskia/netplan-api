import io
import threading

import simplejson as json
import yaml  # PyYAML
from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder

from core.log import logger
from model import models
from service.netplan import NetplanService, get_netplan_service
from utils.os_utils import delayed_netplan_change


router = APIRouter()


@router.get("/get_eth_interfaces")
async def get_interfaces1(
    netplan_service: NetplanService = Depends(get_netplan_service),
):
    try:
        # test: http://localhost:8080/get_interfaces1
        return await netplan_service.get_eth_interfaces()
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submitBridge")
async def submitBridge(data: models.SubmitBridge):
    try:
        debug = False
        data = jsonable_encoder(data)

        if debug:
            logger.debug(f"submitBridge >> data = {json.dumps(data)}")

        # create netplan objects (https://netplan.io/)
        netplan_bridge = {
            "br0": {
                "interfaces": ["eth0", "eth1"],
                "routes": [{"to": "default", "via": data["gateway"]}],
                "addresses": data["addresses"],
                "nameservers": {"addresses": data["nameservers"]},
            }
        }
        netplan_ethernet = {
            "eth0": {
                "dhcp4": False,
                "match": {"macaddress": data["mac1"]},
                "set-name": "eth0",
            },
            "eth1": {
                "dhcp4": False,
                "match": {"macaddress": data["mac2"]},
                "set-name": "eth1",
            },
        }
        if debug:
            logger.debug("netplan_bridge = " + json.dumps(netplan_bridge))

        # get netplan file
        with open(NETPLAN, "r") as stream:
            try:
                netplan_config = yaml.safe_load(stream)
                if debug:
                    logger.debug("netplan_config = " + json.dumps(netplan_config))
                stream.close()
            except yaml.YAMLError as e:
                logger.error(f"error = {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # update netplan file
        netplan_config["network"]["bridges"] = netplan_bridge
        netplan_config["network"]["ethernets"] = netplan_ethernet

        # remove unused values
        if not data["gateway"]:
            del netplan_config["network"]["bridges"]["br0"]["routes"]
            del netplan_config["network"]["bridges"]["br0"]["nameservers"]

        # write netplan changes
        with io.open(NETPLAN, "w", encoding="utf8") as outfile:
            yaml.dump(
                netplan_config, outfile, default_flow_style=False, allow_unicode=True
            )

        # apply changes
        thr = threading.Thread(target=delayed_netplan_change)
        thr.start()

        return {"response": "OK"}
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submitEth1")
async def submitEth1(data: models.SubmitEth):
    try:
        debug = True
        data = jsonable_encoder(data)

        if debug:
            logger.debug(f"data = {json.dumps(data)}")

        # create netplan objects (https://netplan.io/)
        if data["dhcp"]:
            netplan_eth1 = {
                "dhcp4": True,
                "dhcp6": False,
                "match": {"macaddress": data["mac"]},
                "set-name": "eth0",
            }
        else:
            netplan_eth1 = {
                "dhcp4": False,
                "dhcp6": False,
                "match": {"macaddress": data["mac"]},
                "set-name": "eth0",
                "routes": [{"to": "default", "via": data["gateway"]}],
                "addresses": data["addresses"],
                "nameservers": {"addresses": data["nameservers"]},
            }
        if debug:
            logger.debug("netplan_eth1 = " + json.dumps(netplan_eth1))

        # get netplan file
        with open(NETPLAN, "r") as stream:
            try:
                netplan_config = yaml.safe_load(stream)  # dictionary, not list
                if debug:
                    logger.debug("netplan_config = " + json.dumps(netplan_config))
                stream.close()
            except yaml.YAMLError as e:
                logger.error(f"error = {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # update netplan file
        if "ethernets" in netplan_config["network"]:
            netplan_config["network"]["ethernets"]["eth0"] = netplan_eth1
        else:
            netplan_config["network"]["ethernets"] = {}
            netplan_config["network"]["ethernets"]["eth0"] = netplan_eth1

        # remove unused values
        if data["deleteEth"]:
            if "ethernets" in netplan_config["network"]:
                if "eth0" in netplan_config["network"]["ethernets"]:
                    del netplan_config["network"]["ethernets"]["eth0"]
        else:
            if "bridges" in netplan_config["network"]:
                del netplan_config["network"]["bridges"]
            if not data["gateway"]:
                if "routes" in netplan_config["network"]["ethernets"]["eth0"]:
                    del netplan_config["network"]["ethernets"]["eth0"]["routes"]

        # write netplan changes
        with io.open(NETPLAN, "w", encoding="utf8") as outfile:
            yaml.dump(
                netplan_config, outfile, default_flow_style=False, allow_unicode=True
            )

        # apply changes
        thr = threading.Thread(target=delayed_netplan_change)
        thr.start()

        return {"response": "OK"}
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submitEth2")
async def submitEth2(data: models.SubmitEth):
    try:
        debug = True
        data = jsonable_encoder(data)

        if debug:
            logger.debug(f"data = {json.dumps(data)}")

        # create netplan objects (https://netplan.io/)
        if data["dhcp"]:
            netplan_eth2 = {
                "dhcp4": True,
                "dhcp6": False,
                "match": {"macaddress": data["mac"]},
                "set-name": "eth1",
            }
        else:
            netplan_eth2 = {
                "dhcp4": False,
                "dhcp6": False,
                "match": {"macaddress": data["mac"]},
                "set-name": "eth1",
                "routes": [{"to": "default", "via": data["gateway"]}],
                "addresses": data["addresses"],
                "nameservers": {"addresses": data["nameservers"]},
            }
        if debug:
            logger.debug("netplan_eth2 = " + json.dumps(netplan_eth2))

        # get netplan file
        with open(NETPLAN, "r") as stream:
            try:
                netplan_config = yaml.safe_load(stream)
                if debug:
                    logger.debug("netplan_config = " + json.dumps(netplan_config))
                stream.close()
            except yaml.YAMLError as e:
                logger.error(f"error = {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # update netplan file
        if "ethernets" in netplan_config["network"]:
            netplan_config["network"]["ethernets"]["eth1"] = netplan_eth2
        else:
            netplan_config["network"]["ethernets"] = {}
            netplan_config["network"]["ethernets"]["eth1"] = netplan_eth2

        # remove unused values
        if data["deleteEth"]:
            if "ethernets" in netplan_config["network"]:
                if "eth1" in netplan_config["network"]["ethernets"]:
                    del netplan_config["network"]["ethernets"]["eth1"]
        else:
            if "bridges" in netplan_config["network"]:
                del netplan_config["network"]["bridges"]
            if not data["gateway"]:
                if "routes" in netplan_config["network"]["ethernets"]["eth1"]:
                    del netplan_config["network"]["ethernets"]["eth1"]["routes"]

        # write netplan changes
        with io.open(NETPLAN, "w", encoding="utf8") as outfile:
            yaml.dump(
                netplan_config, outfile, default_flow_style=False, allow_unicode=True
            )

        # apply changes
        thr = threading.Thread(target=delayed_netplan_change)
        thr.start()

        return {"response": "OK"}
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
