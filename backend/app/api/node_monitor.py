from fastapi import APIRouter, HTTPException, WebSocket, BackgroundTasks
from ..celery_config import redis_client
import psutil
import os
import logging
import asyncio
import json
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

NODE_STATS_PREFIX = "node_stats:"
NODE_EXPIRY_SECONDS = 10 # 節點狀態在 Redis 中的過期時間 (例如 10 秒)

def get_current_node_name():
    # 保持原有的節點命名邏輯，確保唯一性
    # 如果 PORT 環境變數不可靠或不明確，需要找到更可靠的方式來命名節點
    # 例如，可以是 Docker 容器的 hostname 或一個唯一的 ID
    return f"node{os.getenv('PORT', 'unknown')[-1]}" # 稍微修改以應對 PORT 未設定的情況

def get_node_stats():
    try:
        cpu_percent = psutil.cpu_percent(interval=None) # interval=None for non-blocking
        memory = psutil.virtual_memory()
        # node_name 在外部產生並傳入，或在這裡產生
        return {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory.percent, 1),
            "memory_used_mb": round(memory.used / 1024 / 1024, 1),
            "memory_total_mb": round(memory.total / 1024 / 1024, 1)
        }
    except Exception as e:
        logger.exception("獲取本機節點狀態失敗: %s", str(e))
        return None

async def update_node_stats_in_redis():
    """定期獲取本機節點狀態並更新到 Redis"""
    node_name = get_current_node_name()
    redis_key = f"{NODE_STATS_PREFIX}{node_name}"
    while True:
        try:
            stats = get_node_stats()
            if stats:
                # 將節點名稱加入到 stats 中，以便前端知道是哪個節點
                stats_with_name = {"node": node_name, **stats}
                redis_client.setex(redis_key, NODE_EXPIRY_SECONDS, json.dumps(stats_with_name))
                logger.debug(f"節點 {node_name} 狀態已更新到 Redis: {stats_with_name}")
            else:
                logger.warning(f"節點 {node_name} 無法獲取狀態，從 Redis 中移除 (或標記為不活躍)")
                # 可以選擇刪除鍵，或保留但標記為不活躍
                # redis_client.delete(redis_key)
        except Exception as e:
            logger.exception(f"更新節點 {node_name} 狀態到 Redis 失敗: {str(e)}")
        await asyncio.sleep(1) # 每秒更新一次

@router.on_event("startup")
async def startup_event():
    # 啟動背景任務來持續更新此節點的狀態到 Redis
    # 這確保了每個 node_monitor.py 實例都會上報自己的狀態
    asyncio.create_task(update_node_stats_in_redis())
    logger.info("節點狀態更新背景任務已啟動。")


@router.get("/nodes")
async def list_all_node_stats():
    """從 Redis 獲取所有活動節點的狀態"""
    nodes_data = []
    try:
        # 掃描所有符合模式的鍵
        for key in redis_client.scan_iter(f"{NODE_STATS_PREFIX}*"):
            node_data_json = redis_client.get(key)
            if node_data_json:
                try:
                    nodes_data.append(json.loads(node_data_json))
                except json.JSONDecodeError:
                    logger.error(f"無法解析 Redis 中的節點數據: {key.decode('utf-8')}")
        
        if not nodes_data:
            logger.info("Redis 中沒有找到節點狀態數據。")
            # 可以回傳空列表或特定訊息
            # raise HTTPException(status_code=404, detail="沒有可用的節點狀態")

        return {"nodes": nodes_data}
    except Exception as e:
        logger.exception("從 Redis 列出節點狀態失敗: %s", str(e))
        raise HTTPException(status_code=500, detail=f"列出節點狀態失敗: {str(e)}")

@router.websocket("/ws/nodes")
async def websocket_all_nodes(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            nodes_data = []
            try:
                for key in redis_client.scan_iter(f"{NODE_STATS_PREFIX}*"):
                    node_data_json = redis_client.get(key)
                    if node_data_json:
                        try:
                            nodes_data.append(json.loads(node_data_json))
                        except json.JSONDecodeError:
                            logger.error(f"WebSocket: 無法解析 Redis 中的節點數據: {key.decode('utf-8')}")
                
                if nodes_data:
                    await websocket.send_text(json.dumps({"nodes": nodes_data}))
                    logger.debug(f"WebSocket 推送 {len(nodes_data)} 個節點狀態")
                else:
                    # 如果沒有數據，可以選擇不發送，或發送空列表/特定訊息
                    await websocket.send_text(json.dumps({"nodes": []})) # 或者 {"message": "等待節點數據..."}
                    logger.debug("WebSocket: Redis 中沒有找到節點狀態數據，推送空列表。")

            except Exception as e: # 捕捉 Redis 相關錯誤
                logger.exception("WebSocket: 從 Redis 獲取節點狀態時發生錯誤: %s", str(e))
                await websocket.send_text(json.dumps({"error": "無法從 Redis 獲取節點狀態"}))
            
            await asyncio.sleep(1) # 每秒推送一次
    except Exception as e: # 捕捉 WebSocket 連接等錯誤
        logger.exception("WebSocket 錯誤: %s", str(e))
    finally:
        logger.info(f"WebSocket 連接已關閉: {websocket.client}")
        await websocket.close()