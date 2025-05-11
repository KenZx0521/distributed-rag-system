from fastapi import APIRouter, HTTPException, WebSocket
from celery.result import AsyncResult
from ..celery_config import app as celery_app, redis_client
import logging
import json
import asyncio

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    try:
        task = AsyncResult(task_id, app=celery_app)
        if not task.ready():
            return {
                "task_id": task_id,
                "status": task.state,
                "node": task.info.get("node", "unknown") if task.info else "unknown"
            }
        result = task.result if task.state == "SUCCESS" else None
        error = task.info.get("error", None) if task.state == "FAILED" else None
        return {
            "task_id": task_id,
            "status": task.state,
            "node": task.info.get("node", "unknown") if task.info else "unknown",
            "result": result,
            "error": error
        }
    except Exception as e:
        logger.exception("查詢任務狀態失敗: %s", str(e))
        raise HTTPException(status_code=500, detail=f"查詢任務狀態失敗: {str(e)}")

@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    try:
        task = AsyncResult(task_id, app=celery_app)
        if task.state == "PENDING":
            task.revoke()
            redis_client.srem('task_ids', task_id)
            logger.debug("任務 %s 已取消", task_id)
            return {"message": f"任務 {task_id} 已取消"}
        else:
            logger.warning("無法取消任務 %s，當前狀態: %s", task_id, task.state)
            raise HTTPException(status_code=400, detail="僅能取消排隊中的任務")
    except Exception as e:
        logger.exception("取消任務失敗: %s", str(e))
        raise HTTPException(status_code=500, detail=f"取消任務失敗: {str(e)}")

@router.get("/tasks")
async def list_tasks():
    try:
        task_ids = redis_client.smembers('task_ids')
        tasks = []
        for task_id in task_ids:
            task = AsyncResult(task_id, app=celery_app)
            task_data = {
                "task_id": task_id,
                "status": task.state,
                "node": task.info.get("node", "unknown") if task.info else "unknown"
            }
            if task.ready():
                task_data["result"] = task.result if task.state == "SUCCESS" else None
                task_data["error"] = task.info.get("error", None) if task.state == "FAILED" else None
            tasks.append(task_data)
        logger.debug("返回任務列表，數量: %d", len(tasks))
        return {"tasks": tasks}
    except Exception as e:
        logger.exception("列出任務失敗: %s", str(e))
        raise HTTPException(status_code=500, detail=f"列出任務失敗: {str(e)}")

@router.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            task_ids = redis_client.smembers('task_ids')
            tasks = []
            for task_id in task_ids:
                task = AsyncResult(task_id, app=celery_app)
                task_data = {
                    "task_id": task_id,
                    "status": task.state,
                    "node": task.info.get("node", "unknown") if task.info else "unknown"
                }
                if task.ready():
                    task_data["result"] = task.result if task.state == "SUCCESS" else None
                    task_data["error"] = task.info.get("error", None) if task.state == "FAILED" else None
                tasks.append(task_data)
            
            logger.debug("WebSocket 推送任務列表，數量: %d，狀態: %s", 
                        len(tasks), 
                        {task["task_id"]: task["status"] for task in tasks})
            await websocket.send_text(json.dumps({"tasks": tasks}))
            await asyncio.sleep(1)
    except Exception as e:
        logger.exception("WebSocket 錯誤: %s", str(e))
    finally:
        await websocket.close()