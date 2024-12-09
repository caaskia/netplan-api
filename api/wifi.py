# api/wifi.py

import asyncio

from fastapi import APIRouter, HTTPException, Form, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.config import logger
from model.models import BaseWiFiData, UpdateWiFiData
from service.netplan import NetplanService, get_netplan_service
from utils.ip_utils import (
    get_net_iface,
    get_wifi_ssids,
    get_current_wifi_info,
    get_available_wifi,
    is_wifi_connected, disconnect_wifi,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

connected_flag = False


async def wait_for_connection(iwface: str):
    """Функция ожидания подключения Wi-Fi."""
    global connected_flag

    for _ in range(15):
        if is_wifi_connected():
            connected_flag = True
            break
        await asyncio.sleep(1)
    else:
        connected_flag = False


@router.get("/checkConnection", response_class=JSONResponse)
async def check_connection():
    # if is_wifi_connected():
    if connected_flag:
        logger.info("Wi-Fi соединение установлено")
        return {"connected": True}
    return {"connected": False}


@router.get("/getWiFi", response_class=HTMLResponse)
async def get_wifi(request: Request):
    try:
        # Проверяем текущее состояние Wi-Fi
        # available_networks = get_available_wifi()
        # for network in available_networks:
        #     fields = network.split(":")
        #     if "*" in fields[0]:  # Активное соединение помечено '*'

        if is_wifi_connected():
            wifi_info = get_current_wifi_info()
            ip_addresses = wifi_info.get("ip_addresses")
            ip_addr_static = wifi_info.get("ip_addr_static")
            if ip_addr_static not in ip_addresses:
                wifi_info["ip_addr_static"] = (
                    'Нажмите кнопку "Update" для добавления статического адреса'
                )
            return templates.TemplateResponse(
                "wifi_info_form.html", {"request": {}, "wifi_info": wifi_info}
            )
        # Если активного соединения нет, возвращаем форму для подключения
        ssids = get_wifi_ssids()
        return templates.TemplateResponse(
            "wifi_form.html", {"request": request, "ssids": ssids}
        )

    except Exception as e:
        logger.error(f"Error checking Wi-Fi status: {e}")
        raise HTTPException(status_code=500, detail="Unable to check Wi-Fi status")


@router.post("/connectWiFi")
async def connect_wifi(
    request: Request,
    ssid: str = Form(...),
    ssid_password: str = Form(...),
    netplan_service: NetplanService = Depends(get_netplan_service),
):
    global connected_flag
    connected_flag = False

    try:
        interfaces = get_net_iface()  # список интерфейсов
        iwface = None

        for iface, iface_type in interfaces.items():
            if iface_type == "wlan":  # Проверяем, что это интерфейс Wi-Fi
                iwface = iface
                break

        if not iwface:
            raise HTTPException(status_code=404, detail="Wi-Fi interface not found")

        data = BaseWiFiData(ssid=ssid, ssidPassword=ssid_password, iwface=iwface)

        if not await netplan_service.create_conn_wifi(data):
            raise HTTPException(status_code=500, detail="Error writing netplan file")

        await netplan_service.apply_conn_wifi()
        asyncio.create_task(wait_for_connection(iwface))
        return templates.TemplateResponse(
            "loading.html",
            {
                "request": request,
                "check_url": "/api/wifi/checkConnection",
                "redirect_url": "/api/wifi/getWiFi",
                "attempt_count": 0,
            },
        )
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/updateWiFi", response_class=HTMLResponse)
async def get_update_wifi_data():
    """
    Возвращает HTML-форму для создания Wi-Fi конфигурации.
    """
    wifi_info = get_current_wifi_info()

    return templates.TemplateResponse(
        "wifi_update_form.html", {"request": {}, "wifi_info": wifi_info}
    )


@router.post("/updateWiFi")
async def update_wifi(
    ssid: str = Form(...),
    ssid_password: str = Form(...),
    iwface: str = Form(...),
    ip_addr_static: str = Form(...),
    nameservers: str = Form(...),
    netplan_service: NetplanService = Depends(get_netplan_service),
):
    """
    Обрабатывает данные формы и настраивает Wi-Fi через Netplan.
    """
    global connected_flag
    connected_flag = False
    try:
        # Разделяем строку nameservers на список

        nameservers_list = (
            [ns.strip() for ns in nameservers.split(",")] if nameservers else None
        )

        wifi_data = UpdateWiFiData(
            ssid=ssid,
            ssidPassword=ssid_password,
            iwface=iwface,
            addresses=[
                ip_addr_static,
            ],
            nameservers=nameservers_list,
        )

        # Обновляем Wi-Fi конфигурацию
        if not await netplan_service.update_wifi(wifi_data.model_dump()):
            raise HTTPException(status_code=500, detail="Error update netplan file")

        disconnected = disconnect_wifi()
        await netplan_service.apply_conn_wifi()
        asyncio.create_task(wait_for_connection(iwface))
        return templates.TemplateResponse(
            "loading.html",
            {
                "request": {},
                "check_url": "/api/wifi/checkConnection",
                "redirect_url": "/api/wifi/getWiFi",
                "attempt_count": 0,
            },
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}
