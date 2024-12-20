# core/config.py

import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from core.log import logger

env_path = Path(__file__).resolve().parent / ".env"
logger.info(f"env_path - {env_path}")  # Используем логгер для информации


class Settings(BaseSettings):
    class Config:
        extra = "allow"
        env_file = ".env"  # or your specific env file path

    debug: bool = True
    netplan_eth: str = Field("/etc/netplan/20-static-ip.yaml", alias="NETPLAN_ETH")
    netplan_wifi: str = Field("/etc/netplan/30-wifi-static.yaml", alias="NETPLAN_WIFI")
    netplan_wifi01: str = Field(
        "/etc/netplan/31-wifi-static.yaml", alias="NETPLAN_WIFI01"
    )
    netplan_br: str = Field("/etc/netplan/01-netcfg.yaml", alias="NETPLAN_BRIDGE")


settings = Settings()

formatted_settings = json.dumps(settings.model_dump(), indent=4)
logger.info(f"Settings: {formatted_settings}")
