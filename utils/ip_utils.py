# utils/ip_utils.py

import subprocess

import netifaces  # netifaces2


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
