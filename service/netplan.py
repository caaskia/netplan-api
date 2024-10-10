from functools import lru_cache

import simplejson as json
import yaml
from fastapi import HTTPException

import log
from core.config import settings

logger = log.setup_custom_logger("root")


class NetplanService:
    def __init__(self):
        self.name = "systemd_service"

    @staticmethod
    def get_network(netplan_config):
        with open(netplan_config, "r") as stream:
            try:
                netplan_config = yaml.safe_load(stream)
                if settings.debug:
                    logger.debug("netplan_config = " + json.dumps(netplan_config))
                stream.close()
            except yaml.YAMLError as e:
                logger.error(f"error = {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        network = netplan_config.get("network")
        if settings.debug:
            logger.debug("network = " + json.dumps(network))
        return network

    async def get_eth_interfaces(self):
        ifaces = {}
        network = self.get_network(settings.netplan_eth)

        ethernets = network.get("ethernets", "")
        if ethernets:
            if settings.debug:
                logger.debug("ethernets = " + json.dumps(ethernets))
            for key, value in ethernets.items():
                iface = {}
                iface["dhcp"] = value.get("dhcp4", False)
                iface["addresses"] = value.get("addresses", "")
                routes = value.get("routes", "")
                if routes:
                    iface["gateway"] = routes[0].get("via", "")
                nameservers = value.get("nameservers", "")
                if nameservers:
                    iface["nameservers"] = nameservers.get("addresses", "")
                match = value.get("match", "")
                if match:
                    iface["mac"] = match.get("macaddress", "")
                ifaces[key] = iface
        return ifaces

    async def get_wifi_interfaces(self):
        debug = True
        ifaces = {}

        network = self.get_network(settings.netplan_wifi)
        wifis = network.get("wifis", "")
        if wifis:
            if debug:
                logger.debug("wifis = " + json.dumps(wifis))
            for key, value in wifis.items():
                iface = {}
                iface["dhcp"] = value.get("dhcp4", False)
                iface["addresses"] = value.get("addresses", "")
                routes = value.get("routes", "")
                if routes:
                    iface["gateway"] = routes[0].get("via", "")
                nameservers = value.get("nameservers", "")
                if nameservers:
                    iface["nameservers"] = nameservers.get("addresses", "")

                wifi_access_points = value.get("access-points", "")
                for key in wifi_access_points.keys():
                    iface["ssid"] = key
                    iface["ssid_password"] = wifi_access_points[key].get("password", {})

                ifaces[key] = iface
        if debug:
            logger.info(f"ifaces = {json.dumps(ifaces)}")
        return ifaces

    async def get_br_interfaces(self):
        debug = True
        ifaces = {}

        network = self.get_network(settings.netplan_wifi)
        bridges = network.get("bridges", "")
        if bridges:
            if settings.debug:
                logger.debug("bridges = " + json.dumps(bridges))

            for key, value in bridges.items():
                iface = {}
                br0 = bridges.get("br0", "")
                if br0:
                    br0_addresses = br0.get("addresses", "")
                    routes = br0.get("routes", "")
                    nameservers = br0.get("nameservers", "")
                    if routes:
                        br0_gateway = routes[0].get("via", "")
                    if nameservers:
                        br0_nameservers = nameservers.get("addresses", "")
        if debug:
            logger.info(f"ifaces = {json.dumps(ifaces)}")
        return ifaces


@lru_cache()
def get_netplan_service() -> NetplanService:
    return NetplanService()
