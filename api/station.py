import os
import threading
from fastapi import APIRouter, HTTPException

from utils.os_utils import delayed_reboot, delayed_shutdown

from core.config import logger

router = APIRouter()


@router.get("/reboot_station")
async def reboot_station():
    try:
        thr = threading.Thread(target=delayed_reboot)
        thr.start()
        return {"response": "OK"}
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shutdown_station")
async def shutdown_station():
    try:
        thr = threading.Thread(target=delayed_shutdown)
        thr.start()
        return {"response": "OK"}
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clear_all_log_files")
async def clear_all_log_files():
    try:
        EXECUTABLE = "rm -f /var/www/html/logs/*.log"
        os.system(EXECUTABLE)
        return {"response": "OK"}
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/change_log_file_perm")
async def change_log_file_perm():
    try:
        EXECUTABLE = "chmod -R 777 /var/www/html/logs"
        os.system(EXECUTABLE)
        return {"response": "OK"}
    except Exception as e:
        logger.error(f"error = {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
