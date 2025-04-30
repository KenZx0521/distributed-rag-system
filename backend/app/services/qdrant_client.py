from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid
import json
import os
import logging

# 配置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self, host="qdrant", port=6333):
        logger.debug("初始化 QdrantService，連接到 %s:%d", host, port)
        try:
            self.client = QdrantClient(host=host, port=port)
            logger.debug("Qdrant 客戶端初始化成功")
        except Exception as e:
            logger.exception("Qdrant 客戶端初始化失敗: %s", str(e))
            raise
        self.collection_name = "KnowledgeBase"
        self.vectorizer = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_dim = 384
        self.json_file_path = os.path.join(os.getcwd(), "data", "data.json")

    def create_collection(self):
        logger.debug("檢查並創建集合: %s", self.collection_name)
        try:
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE)
                )
                logger.debug("集合 %s 創建成功", self.collection_name)
            else:
                logger.debug("集合 %s 已存在", self.collection_name)
        except Exception as e:
            logger.exception("創建集合失敗: %s", str(e))
            raise

    def store_data(self, data_list):
        logger.debug("開始儲存 %d 條數據", len(data_list))
        
        # 確保集合存在
        self.create_collection()
        
        # 儲存數據到 JSON 檔案
        try:
            os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=4)
            logger.debug("數據已儲存到 %s", self.json_file_path)
        except Exception as e:
            logger.exception("儲存 JSON 檔案失敗: %s", str(e))
            raise

        # 從 JSON 檔案載入數據
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
            logger.debug("從 JSON 檔案載入 %d 條數據", len(data_list))
        except Exception as e:
            logger.exception("載入 JSON 檔案失敗: %s", str(e))
            raise
        
        # 將數據轉為向量並儲存到 Qdrant
        points = []
        batch_size = 100
        for i, data in enumerate(data_list):
            try:
                content = str(data["content"])
                logger.debug("向量化數據 %d: %s", i, content[:50])
                vector = self.vectorizer.encode(content, show_progress_bar=False).tolist()
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "content": content,
                        "source": str(data.get("source", "csv_upload"))
                    }
                )
                points.append(point)
                
                if len(points) >= batch_size or i == len(data_list) - 1:
                    logger.debug("上傳批次，數量: %d", len(points))
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    points = []
            except Exception as e:
                logger.exception("處理數據 %d 失敗: %s", i, str(e))
                raise
        
        logger.debug("所有數據儲存完成")

    def query(self, query_text, limit=5):
        logger.debug("執行查詢: %s", query_text)
        try:
            if not self.client.collection_exists(self.collection_name):
                logger.error("集合 %s 不存在", self.collection_name)
                raise ValueError(f"集合 {self.collection_name} 不存在")
            query_vector = self.vectorizer.encode(query_text, show_progress_bar=False).tolist()
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True
            )
            results = [
                {
                    "content": hit.payload["content"],
                    "source": hit.payload["source"],
                    "score": hit.score
                }
                for hit in search_result
            ]
            logger.debug("查詢返回 %d 條結果", len(results))
            return results
        except Exception as e:
            logger.exception("查詢失敗: %s", str(e))
            raise