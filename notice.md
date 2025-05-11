## 訪問注意事項

## Qdarnt
1. **監控儀錶板**：http://localhost:6333/dashboard
2. **啟動Database**：docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant:latest


### 前端
到frontend啟動npm start，localhost:3000

### 後端
到backend啟動uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
http://localhost:8000/docs
清理Redis：docker exec -it backend-redis-1 redis-cli DEL task_ids

