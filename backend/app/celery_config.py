from celery import Celery
from .services.qdrant_client import QdrantService
from .services.csv_processor import process_csv
import os
import redis
import logging

# 配置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化 Redis 客戶端
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=6379,
    db=0,
    decode_responses=True
)

# 初始化 Celery
app = Celery(
    'rag_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@app.task(bind=True)
def upload_task(self, file_content):
    logger.debug("執行上傳任務: %s", self.request.id)
    try:
        # 儲存任務 ID 到 Redis 集合
        redis_client.sadd('task_ids', self.request.id)
        self.update_state(state='RUNNING', meta={'node': os.getenv('PORT', 'unknown')})
        data_list = process_csv(file_content)
        qdrant_service = QdrantService()
        qdrant_service.store_data(data_list)
        return {"message": "檔案上傳成功，已儲存到知識庫", "records": len(data_list)}
    except Exception as e:
        logger.exception("上傳任務失敗: %s", str(e))
        self.update_state(state='FAILED', meta={'error': str(e)})
        raise

@app.task(bind=True)
def query_task(self, query_text):
    logger.debug("執行查詢任務: %s", self.request.id)
    try:
        # 儲存任務 ID 到 Redis 集合
        redis_client.sadd('task_ids', self.request.id)
        self.update_state(state='RUNNING', meta={'node': os.getenv('PORT', 'unknown')})
        qdrant_service = QdrantService()
        results = qdrant_service.query(query_text, limit=5)
        return {"results": results}
    except Exception as e:
        logger.exception("查詢任務失敗: %s", str(e))
        self.update_state(state='FAILED', meta={'error': str(e)})
        raise