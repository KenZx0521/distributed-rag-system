from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..celery_config import query_task
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.get("/query")
async def get_query():
    return {"message": "Please use POST method to submit a query"}

@router.post("/query")
async def query_knowledge_base(request: QueryRequest):
    logger.debug("收到查詢請求: %s", request.query)
    try:
        task = query_task.delay(request.query)
        return {"task_id": task.id, "message": "任務已提交到隊列"}
    except Exception as e:
        logger.exception("提交任務失敗: %s", str(e))
        raise HTTPException(status_code=500, detail=f"提交任務失敗: {str(e)}")