import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.upload import router as upload_router
from .api.query import router as query_router
from .api.task_manager import router as task_manager_router
import logging

# 配置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Distributed RAG System API")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 掛載路由
app.include_router(upload_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(task_manager_router, prefix="/api")

@app.get("/")
async def root():
    port = os.getenv("PORT", "8000")
    return {"message": f"Welcome to the Distributed RAG System API (Node on port {port})"}