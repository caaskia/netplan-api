import os
import subprocess
import time

from core.log import logger


def delayed_reboot():
    try:
        time.sleep(3)
        EXECUTABLE = "reboot"
        os.system(EXECUTABLE)
    except Exception as e:
        logger.error(f"error = {str(e)}")


def delayed_shutdown():
    try:
        time.sleep(3)
        EXECUTABLE = "shutdown now"
        os.system(EXECUTABLE)
    except Exception as e:
        logger.error(f"error = {str(e)}")


def delayed_netplan_change():
    try:
        subprocess.run(["sync"], check=True)
        time.sleep(1)
        subprocess.run(["sudo", "netplan", "apply"], check=True)
        logger.info("Netplan configuration applied successfully.")

    except subprocess.CalledProcessError as e:
        logger.error(f"Error applying netplan configuration: {str(e)}")


def os_netplan_change():
    try:
        time.sleep(1)
        os.system("sync")  # commit buffer cache to disk
        # generate config for the renderers
        os.system("netplan generate")
        time.sleep(1)
        # apply config for the renderers
        # os.system("netplan apply")
    except Exception as e:
        logger.error(f"error = {str(e)}")


def delayed_vpn_server_change():
    try:
        os.system("sync")  # Synchronize cached writes to persistent storage

        time.sleep(1)
        os.system("service openvpn@server restart")

        time.sleep(3)
        os.system("brctl addif br0 tap0")

        time.sleep(1)
        os.system("ifconfig tap0 0.0.0.0 promisc up")
    except Exception as e:
        logger.error(f"error = {str(e)}")
