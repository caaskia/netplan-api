# api/wifi.py

from fastapi import APIRouter, HTTPException, Form, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.config import logger
from model.models import BaseWiFi, CreateWiFi
from service.netplan import NetplanService, get_netplan_service
from utils.ip_utils import get_net_iface, get_wifi_ssids

router = APIRouter()


# Инициализируем шаблоны
templates = Jinja2Templates(directory="templates")


@router.get("/getWiFi", response_class=HTMLResponse)
async def get_wifi(request: Request):
    ssids = get_wifi_ssids()
    return templates.TemplateResponse(
        "wifi_form.html", {"request": request, "ssids": ssids}
    )


@router.post("/connectWiFi")
async def connect_wifi(
    ssid: str = Form(...),
    ssidPassword: str = Form(...),
    netplan_service: NetplanService = Depends(get_netplan_service),
):
    try:
        data = BaseWiFi(ssid=ssid, ssidPassword=ssidPassword)

        interfaces = get_net_iface()  # список интерфейсов
        iwface = None

        for iface, iface_type in interfaces.items():
            if iface_type == "wlan":  # Проверяем, что это интерфейс Wi-Fi
                iwface = iface
                break

        if not iwface:
            raise HTTPException(status_code=404, detail="Wi-Fi interface not found")

        await netplan_service.create_conn_wifi(data, iwface)
        return {"response": "OK"}
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/createWiFi", response_class=HTMLResponse)
async def get_create_wifi_form():
    """
    Возвращает HTML-форму для создания Wi-Fi конфигурации.
    """
    return templates.TemplateResponse("wifi_update_form.html", {"request": {}})


@router.post("/createWiFi")
async def create_wifi(
    wifi_data: CreateWiFi = Depends(),  # Автоматическое преобразование данных формы
    netplan_service: NetplanService = Depends(get_netplan_service),
):
    """
    Обрабатывает данные формы и настраивает Wi-Fi через Netplan.
    """
    try:
        # Получаем Wi-Fi интерфейс
        interfaces = await netplan_service.get_wifi_interfaces()
        iwface = next(iter(interfaces.keys()), None)  # Первый Wi-Fi интерфейс

        if not iwface:
            raise HTTPException(status_code=404, detail="Wi-Fi interface not found")

        # Обновляем Wi-Fi конфигурацию
        await netplan_service.update_wifi(wifi_data.dict())  # Передаём данные как словарь

        return {"status": "success", "message": "Wi-Fi configuration created successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}



# @router.post("/createWiFi")
# async def create_wifi(
#         gateway: str = Form(...),
#         addresses: str = Form(...),
#         nameservers: str = Form(...),
#         ssid: str = Form(...),
#         ssidPassword: str = Form(...),
#         netplan_service: NetplanService = Depends(get_netplan_service),
# ):
#     try:
#         # Преобразуем адреса и nameservers в списки
#         addresses_list = addresses.split(',')
#         nameservers_list = nameservers.split(',')
#
#         # Создаем объект CreateWiFi
#         data = CreateWiFi(
#             gateway=gateway,
#             addresses=addresses_list,
#             nameservers=nameservers_list,
#             ssid=ssid,
#             ssidPassword=ssidPassword
#         )
#
#         await netplan_service.submit_wifi(data)
#         return {"response": "OK"}
#     except Exception as e:
#         logger.error(f"error = {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
