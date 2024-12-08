import io
import threading
from functools import lru_cache
from pathlib import Path

import simplejson as json
import yaml
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from core.config import settings
from core.log import logger
from model.models import BaseWiFiData, UpdateWiFiData
from utils.os_utils import delayed_netplan_change


class NetplanService:
    def __init__(self):
        self.name = "netplan_service"

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

    @staticmethod
    async def create_conn_wifi(data: BaseWiFiData, iwface: str):
        data = jsonable_encoder(data)
        netplan_config = {}
        debug = settings.debug
        if debug:
            logger.debug(f"data = {json.dumps(data)}")

        # Создание объекта netplan Wi-Fi
        netplan_wifi = {
            "dhcp4": True,  # Используем DHCP для IPv4
            "dhcp6": True,  # Включаем DHCP для IPv6
            "access-points": {data["ssid"]: {"password": data["ssidPassword"]}},
        }

        if debug:
            logger.debug(f"netplan_wifi = {json.dumps(netplan_wifi)}")

        netplan_path = Path(settings.netplan_wifi01)
        if netplan_path.exists():
            try:
                with open(netplan_path, "r") as stream:
                    netplan_config = yaml.safe_load(stream)
                    if debug:
                        logger.debug(f"netplan_config = {json.dumps(netplan_config)}")
            except yaml.YAMLError as e:
                logger.error(f"Error reading netplan file: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Error reading netplan file"
                )

        if "network" not in netplan_config:
            netplan_config["network"] = {}
            netplan_config["network"]["version"] = 2
            netplan_config["network"]["renderer"] = "NetworkManager"

        # Обновление или создание записи для Wi-Fi интерфейса (например, wlan0)
        if "wifis" not in netplan_config["network"]:
            netplan_config["network"]["wifis"] = {}

        # Обновляем конфигурацию Wi-Fi для заданного интерфейса (iwface)
        netplan_config["network"]["wifis"][iwface] = netplan_wifi

        if debug:
            logger.debug(f"Updated netplan_config = {json.dumps(netplan_config)}")

        # Запись изменений обратно в файл Netplan
        try:
            with io.open(settings.netplan_wifi01, "w", encoding="utf8") as outfile:
                yaml.dump(
                    netplan_config,
                    outfile,
                    default_flow_style=False,
                    allow_unicode=True,
                )
        except Exception as e:
            logger.error(f"Error writing netplan file: {str(e)}")
            raise HTTPException(status_code=500, detail="Error writing netplan file")

        # Применение изменений через команду netplan
        logger.info("Applying netplan changes...")
        thr = threading.Thread(target=delayed_netplan_change)
        thr.start()

    async def update_wifi(self, data: UpdateWiFiData):
        debug = settings.debug
        data = jsonable_encoder(data)

        if debug:
            logger.debug(f"data = {json.dumps(data)}")

        # create netplan objects (https://netplan.io/)
        netplan_wifi = {
            "dhcp4": False,
            "dhcp6": False,
            "addresses": data["addresses"],
            "routes": [{"to": "default", "via": data["gateway"]}],
            "nameservers": {"addresses": data["nameservers"]},
            "access-points": {data["ssid"]: {"password": data["ssidPassword"]}},
        }
        netplan_ap_no_password = {data["ssid"]: {}}

        if debug:
            logger.debug("netplan_wifi = " + json.dumps(netplan_wifi))

        # get netplan file
        with open(settings.netplan_wifi, "r") as stream:
            try:
                netplan_config = yaml.safe_load(stream)
                if debug:
                    logger.debug("netplan_config = " + json.dumps(netplan_config))
                stream.close()
            except yaml.YAMLError as e:
                logger.error(f"error = {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # update netplan file
        netplan_config["network"]["wifis"]["wlp1s0"] = netplan_wifi
        if not data["ssidPassword"]:
            netplan_config[["network"]["wifis"]["wlp1s0"]["access-points"]] = (
                netplan_ap_no_password
            )

        # remove unused values
        if data["deleteWiFi"]:
            if "wifis" in netplan_config["network"]:
                del netplan_config["network"]["wifis"]
        else:
            if not data["gateway"]:
                del netplan_config["network"]["wifis"]["wlp1s0"]["routes"]

        # write netplan changes
        with io.open(settings.netplan_wifi01, "w", encoding="utf8") as outfile:
            yaml.dump(
                netplan_config, outfile, default_flow_style=False, allow_unicode=True
            )

        # apply changes
        thr = threading.Thread(target=delayed_netplan_change)
        thr.start()


@lru_cache()
def get_netplan_service() -> NetplanService:
    return NetplanService()
