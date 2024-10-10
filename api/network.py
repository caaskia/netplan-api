import subprocess

import simplejson as json
from fastapi import APIRouter, HTTPException, Query

from core.config import logger
from model.models import InterfaceName

router = APIRouter()


@router.get("/get_ip_a")
async def get_ip_a():
    try:
        # test: http://localhost:8080/get_ip_a
        debug = False
        ret_obj = {}

        ret_obj["response"] = subprocess.getoutput("ip a")
        if debug:
            logger.info(f"ret_obj = {json.dumps(ret_obj)}")

        return ret_obj
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_status_iface")
async def get_status_iface(
    iface: InterfaceName = Query(
        InterfaceName.enp4s0.value, description="Выберите интерфейс"
    ),
):
    try:
        # test: http://localhost:8080/get_eth0_status
        debug = False
        ret_obj = {}

        ret_obj["response"] = subprocess.getoutput(
            f"grep '' /sys/class/net/{iface}/operstate"
        )
        if debug:
            logger.info(f"ret_obj = {json.dumps(ret_obj)}")

        return ret_obj
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
