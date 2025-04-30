from fastapi import APIRouter, UploadFile, File, HTTPException
from ..celery_config import upload_task
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/upload")
async def get_upload():
    return {"message": "Please use POST method to upload a CSV file"}

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    logger.debug("收到上傳請求，檔案名稱: %s", file.filename)
    if file.content_type != "text/csv":
        logger.error("無效的檔案類型: %s", file.content_type)
        raise HTTPException(status_code=400, detail="僅支援 CSV 檔案")
    
    try:
        content = await file.read()
        logger.debug("檔案大小: %d bytes", len(content))
        task = upload_task.delay(content)
        return {"task_id": task.id, "message": "任務已提交到隊列"}
    except Exception as e:
        logger.exception("提交任務失敗: %s", str(e))
        raise HTTPException(status_code=500, detail=f"提交任務失敗: {str(e)}")