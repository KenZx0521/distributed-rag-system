import pandas as pd
from io import StringIO
import logging

# 配置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_csv(file_content):
    try:
        # 將檔案內容轉為字符串
        content = file_content.decode("utf-8")
        logger.debug("開始解析 CSV 內容")
        
        # 使用 pandas 解析 CSV
        df = pd.read_csv(StringIO(content))
        logger.debug("CSV 欄位: %s", df.columns.tolist())
        
        # 確保 content 欄位存在
        if "content" not in df.columns:
            logger.error("CSV 缺少 'content' 欄位")
            raise ValueError("CSV 必須包含 'content' 欄位")
        
        # 清理數據，轉為字符串並移除空值
        data_list = []
        for _, row in df.iterrows():
            content = str(row["content"]).strip() if pd.notna(row["content"]) else ""
            if content:  # 僅處理非空內容
                data_list.append({
                    "content": content,
                    "source": str(row.get("source", "csv_upload")).strip()
                })
        
        logger.debug("解析完成，生成 %d 條數據", len(data_list))
        logger.debug(data_list)
        return data_list
    except Exception as e:
        logger.exception("CSV 解析失敗: %s", str(e))
        raise