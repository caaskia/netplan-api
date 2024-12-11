# model/models.py

from enum import Enum

from pydantic import BaseModel
from typing import List  # needed for python 3.8 and below


class SubmitBridge(BaseModel):
    mac1: str
    mac2: str
    gateway: str
    addresses: List[str]
    nameservers: List[str]


class SubmitEth(BaseModel):
    mac: str
    dhcp: bool
    gateway: str
    addresses: List[str]
    nameservers: List[str]
    deleteEth: bool


class BaseWiFiData(BaseModel):
    ssid: str
    ssidPassword: str
    iwface: str


class UpdateWiFiData(BaseWiFiData):
    addresses: List[str] | None
    nameservers: List[str] | None


class DeleteWiFiData(BaseWiFiData):
    deleteWiFi: bool


class UpdateStationWifi(BaseModel):
    enabled: str  # 1/0
    network_name: str
    network_password: str
    enable_bridge: str  # 1/0
    network_ap_gateway: str


class InterfaceName(str, Enum):
    enp4s0 = "enp4s0"
    eth0 = "eth0"
    eth1 = "eth1"
    wlan0 = "wlan0"
