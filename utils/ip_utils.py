# utils/ip_utils.py

import subprocess

import netifaces  # netifaces2


def get_iface_gateway_00(iface = 'default'):
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
        print(f"Failed to retrieve gateway for interface '{iface}': {e}")
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
        print(f"Failed to retrieve IP addresses: {e}")
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
        print(f"Failed to retrieve network interfaces: {e}")
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
            print(f"Error executing nmcli: {result.stderr}")
            return []

        # Разбиваем результат на строки и убираем пустые SSID
        ssid_list = [line for line in result.stdout.splitlines() if line.strip()]
        return ssid_list
    except Exception as e:
        print(f"Failed to retrieve Wi-Fi SSIDs: {e}")
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
            print(f"Error executing nmcli: {result.stderr}")
            return None
        return result.stdout.splitlines()
    except Exception as e:
        print(f"Failed to retrieve current Wi-Fi connection info: {e}")
        return None

def get_device_status():
    """
    nmcli -t -f DEVICE,CONNECTION,STATE device status
    """
    try:

        # Получаем интерфейс
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,CONNECTION,STATE", "device", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error executing nmcli: {result.stderr}")
            return None
        return result.stdout.splitlines()
    except Exception as e:
        print(f"Failed to retrieve current Wi-Fi connection info: {e}")
        return None


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
                    if ssid in iface_line:  # Ищем SSID в статусе интерфейса
                        wifi_info["iface"] = iface_line.split(":")[0]
                        break

                # Используем netifaces для получения IP-адреса и шлюза
                if "iface" in wifi_info:
                    iface = wifi_info["iface"]
                    if netifaces.AF_INET in netifaces.ifaddresses(iface):
                        addr_info = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]
                        wifi_info["ip_addr_wifi"] = addr_info.get("addr")
                    gw_wifi = get_iface_gateway(iface)
                    if gw_wifi:
                        print(f"Gateway for Wi-Fi: {gw_wifi}")
                        wifi_info["gw_wifi"] = gw_wifi
                return wifi_info
        print("No active Wi-Fi connection found.")
        return None
    except Exception as e:
        print(f"Failed to retrieve current Wi-Fi connection info: {e}")
        return None


if __name__ == "__main__":
    interfaces = get_net_iface()

    current_wifi = get_current_wifi_info()
    if current_wifi:
        print("Current Wi-Fi connection info:")
        for key, value in current_wifi.items():
            print(f"{key}: {value}")
    else:
        print("No active Wi-Fi connection.")
