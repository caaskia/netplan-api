# utils/ip_utils.py


import subprocess

import netifaces  # netifaces2

from core.config import logger


def is_wifi_connected() -> bool:
    """Проверяет, подключен ли Wi-Fi с использованием nmcli."""
    try:
        result = subprocess.run(
            # ["nmcli", "-t", "-f", "in-use,ssid", "dev", "wifi",  "|",  "grep", "^*"],
            ["nmcli", "-t", "-f", "in-use,ssid", "dev", "wifi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0 and "*:" in result.stdout:
            return True  # Если Wi-Fi подключен
        return False
    except Exception as e:
        return False


def is_wifi_connected_iwgetid(iwface: str) -> bool:
    """Проверяет, подключен ли интерфейс Wi-Fi."""
    try:
        result = subprocess.run(
            ["iwgetid", iwface],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode == 0  # Если команда выполнена успешно
    except Exception as e:
        return False


def get_iface_gateway_00(iface="default"):
    gateways = netifaces.gateways()
    for key, value in gateways.items():
        if iface in value[0]:
            gateway_iface = value[0][0]
            return gateway_iface
    return None


def get_iface_gateway(iface="default"):
    """
    Возвращает шлюз для заданного интерфейса.

    :param iface: Имя интерфейса (например, 'wlp3s0') или 'default' для получения шлюза по умолчанию.
    :return: Шлюз (строка) или None, если не найдено.
    """
    try:
        gateways = netifaces.gateways()
        if iface == "default":
            # Получаем шлюз по умолчанию для IPv4
            default_gateway = gateways.get("default", {}).get(netifaces.AF_INET)
            if default_gateway:
                return default_gateway[0]  # Возвращаем IP-адрес шлюза
        else:
            # Ищем шлюз для конкретного интерфейса
            for gw_type, gw_list in gateways.items():
                if gw_type == netifaces.AF_INET:  # IPv4 шлюзы
                    for gw_entry in gw_list:
                        if gw_entry[1] == iface:  # Если интерфейс совпадает
                            return gw_entry[0]  # Возвращаем IP-адрес шлюза
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve gateway for interface '{iface}': {e}")
        return None


def get_ip_addresses():
    ip_addresses = {}
    try:
        for interface in netifaces.interfaces():
            if interface != "lo":
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    ip_addresses[interface] = [
                        addr_info["addr"] for addr_info in addrs[netifaces.AF_INET]
                    ]
    except Exception as e:
        logger.error(f"Failed to retrieve IP addresses: {e}")
    return ip_addresses


def get_net_iface():
    interfaces = {}
    try:
        for interface in netifaces.interfaces():
            if interface != "lo":  # Исключаем loopback-интерфейс
                if interface.startswith("e"):  # Ethernet интерфейс
                    connection_type = "ethernet"
                elif interface.startswith("wl"):  # Wi-Fi интерфейс
                    connection_type = "wlan"
                elif interface.startswith("ww"):  # Мобильная сеть (WWAN)
                    connection_type = "wwan"
                else:
                    continue
                interfaces[interface] = connection_type
    except Exception as e:
        logger.error(f"Failed to retrieve network interfaces: {e}")
    return interfaces


def get_wifi_ssids():
    try:
        # Выполняем команду nmcli и получаем результат
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID", "device", "wifi", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Проверяем наличие ошибок
        if result.returncode != 0:
            logger.error(f"Error executing nmcli: {result.stderr}")
            return []

        # Разбиваем результат на строки и убираем пустые SSID
        ssid_list = [line for line in result.stdout.splitlines() if line.strip()]
        ssid_list.sort()
        return ssid_list
    except Exception as e:
        logger.error(f"Failed to retrieve Wi-Fi SSIDs: {e}")
        return []


def get_available_wifi():
    """
    Возвращает информацию о текущем Wi-Fi соединении.
    nmcli -t -f IN-USE,SSID,MODE,FREQ,SIGNAL,SECURITY device wifi
    nmcli -t -f ACTIVE,SSID,MODE,FREQ,SIGNAL,SECURITY device wifi
    """
    try:
        # Выполняем команду nmcli и получаем результат
        result = subprocess.run(
            [
                "nmcli",
                "-t",
                "-f",
                "IN-USE,SSID,MODE,FREQ,SIGNAL,SECURITY",
                "device",
                "wifi",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Проверяем наличие ошибок
        if result.returncode != 0:
            logger.error(f"Error executing nmcli: {result.stderr}")
            return None
        return result.stdout.splitlines()
    except Exception as e:
        logger.error(f"Failed to retrieve current Wi-Fi connection info: {e}")
        return None


def get_device_status():
    """
    nmcli -t -f DEVICE,CONNECTION,STATE device status
    """
    try:
        # Получаем интерфейс
        # ["nmcli", "-t", "device", "status"]
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE,CONNECTION,STATE", "device", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"Error executing nmcli: {result.stderr}")
            return None
        return result.stdout.splitlines()
    except Exception as e:
        logger.error(f"Failed to retrieve current Wi-Fi connection info: {e}")
        return None


def get_all_ip_addresses(iface):
    """
    Возвращает список всех IPv4-адресов для указанного интерфейса.

    :param iface: Имя сетевого интерфейса (например, 'wlan0').
    :return: Список IPv4-адресов или пустой список, если нет доступных адресов.
    """
    try:
        # Проверяем, есть ли информация о адресах IPv4
        if netifaces.AF_INET in netifaces.ifaddresses(iface):
            # Извлекаем все адреса IPv4
            addr_infos = netifaces.ifaddresses(iface)[netifaces.AF_INET]
            ip_addresses = [addr_info.get("addr") for addr_info in addr_infos]
            return ip_addresses
    except Exception as e:
        logger.error(f"Failed to retrieve IP addresses for interface '{iface}': {e}")
    return []


def get_current_wifi_info():
    """
    Возвращает информацию о текущем Wi-Fi соединении, включая интерфейс, IP-адрес и шлюз.

    :return: Словарь с информацией о текущем соединении или None, если соединение отсутствует.
    """
    try:
        available_net = get_available_wifi()
        # Ищем активную сеть (ACTIVE == "yes")
        for line in available_net:
            fields = line.split(":")
            if "*" in fields[0].strip().lower():
                ssid = fields[1]
                wifi_info = {
                    "ssid": ssid,
                    "mode": fields[2],
                    "frequency": fields[3],
                    "signal_strength": fields[4],
                    "security": fields[5],
                }

                iface_result = get_device_status()
                for iface_line in iface_result:
                    # if ssid in iface_line:  # Ищем SSID в статусе интерфейса
                    if "wifi" in iface_line:  # Ищем wifi в статусе интерфейса
                        wifi_info["iwface"] = iface_line.split(":")[0]
                        break

                # Используем netifaces для получения IP-адреса и шлюза
                if "iwface" in wifi_info:
                    iwface = wifi_info["iwface"]
                    if netifaces.AF_INET in netifaces.ifaddresses(iwface):
                        # addr_info = netifaces.ifaddresses(iwface)[netifaces.AF_INET][0]
                        addr_infos = netifaces.ifaddresses(iwface)[netifaces.AF_INET]
                        ip_addresses = [
                            addr_info.get("addr") for addr_info in addr_infos
                        ]
                        if ip_addresses:
                            wifi_info["ip_addresses"] = ip_addresses
                            wifi_info["ip_addr"] = ip_addresses
                            ip_addr = ip_addresses[0]

                            ip_addr_static = ".".join(ip_addr.split(".")[:-1]) + ".21"
                            wifi_info["ip_addr_static"] = ip_addr_static

                    gw_wifi = get_iface_gateway(iwface)
                    if gw_wifi:
                        logger.debug(f"Gateway for Wi-Fi: {gw_wifi}")
                        wifi_info["gw"] = gw_wifi
                return wifi_info
        logger.warning("No active Wi-Fi connection found.")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve current Wi-Fi connection info: {e}")
        return None


def disconnect_wifi():
    """Отключает текущее Wi-Fi соединение, используя nmcli."""
    try:
        # Получаем список всех активных устройств и их соединений
        device_status = get_device_status()
        if device_status:
            for line in device_status:
                fields = line.split(":")
                type_iface = fields[1]
                if "wifi" not in type_iface:
                    continue

                device = fields[0]
                connection = fields[2]
                state = fields[3]

                # Если состояние устройства - подключено (connected)
                # ["nmcli", "connection", "down", connection]
                if "connected" in state.lower():
                    # Отключаем Wi-Fi
                    subprocess.run(
                        ["nmcli", "device", "disconnect", device],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    logger.info(f"Disconnected from Wi-Fi connection: {connection}")
                    return True
        logger.warning("No active Wi-Fi connection found to disconnect.")
        return False
    except Exception as e:
        logger.error(f"Failed to disconnect Wi-Fi: {e}")
        return False



if __name__ == "__main__":
    interfaces = get_net_iface()

    current_wifi = get_current_wifi_info()
    if current_wifi:
        logger.info("Current Wi-Fi connection info:")
        for key, value in current_wifi.items():
            logger.info(f"{key}: {value}")
    else:
        logger.warning("No active Wi-Fi connection.")
