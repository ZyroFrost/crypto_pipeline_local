# declarative workflow (định nghĩa pipeline)
from airflow import DAG
from airflow.operators.python import PythonOperator # operator để chạy function Python

from datetime import datetime, timezone, timedelta

import requests, os, json

API_KEY_COINGECKO_URL = os.getenv("API_KEY_COINGECKO_URL")
API_ENDPOINT_COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

GCS_BUCKET_NAME = "zyro-crypto-raw"

OUTPUT_DIR = "/opt/airflow/data/raw" # ường dẫn tuyệt đối trong container

HEADER = {
    "x-cg-demo-api-key": API_KEY_COINGECKO_URL,
}

PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 250,
    "page": 2,
    "sparkline": "false",
}

# Function to fetch crypto data
def fetch_crypto():
    response = requests.get(API_ENDPOINT_COINGECKO_URL, params=PARAMS, headers=HEADER, timeout=10)

    # Check for successful response
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")

    data = response.json() # convert JSON to Python dict/list
    
    # LẤY THỜI GIAN CHUẨN
    now = datetime.now(timezone.utc) # Current UTC time (múi giờ chuẩn quốc tế 0:00 UTC)
    extraction_time = now.strftime("%Y-%m-%d %H:%M:%S") # Định dạng chuẩn cho BigQuery
    date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S") # Timestamp for file naming/tạo tên file unique

    # QUAN TRỌNG: Chèn thêm thời gian vào từng bản ghi để BigQuery dễ query
    # Sửa logic: Kiểm tra nếu là list thì lặp, nếu là dict thì gán trực tiếp để tránh lỗi 'str' object assignment
    if isinstance(data, list):
        for item in data:
            item["extraction_timestamp"] = extraction_time
    else:
        data["extraction_timestamp"] = extraction_time

    folder = f"{OUTPUT_DIR}/{date}" # 
    os.makedirs(folder, exist_ok=True) # Data directory, create if not exists
    file_path = f"{folder}/crypto_{timestamp}.json" # File path with timestamp

    with open(file_path, "w", encoding="utf-8") as f:
        if isinstance(data, list):
            for item in data:
                # Ghi từng object trên một dòng, xóa bỏ indent
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        else:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"[INFO] Saved {len(data)} records → {file_path}")
    print(f"DEBUG: First 200 characters of data: {str(data)[:200]}")

    return file_path # Trả về đường dẫn file để task sau (GCS) có thể sử dụng

# Define DAG
default_args = {
    "owner": "airflow", # name
    "retries": 3, # nếu API fail -> tự retry 3 lần
    "retry_delay": timedelta(minutes=1), # thời gian chờ giữa các lần retry
}

with DAG(
    dag_id="1_crypto_crawler", # tên DAG (hiện trên UI)
    start_date=datetime(2024, 1, 1), # mốc bắt đầu
    # schedule_interval="*/30 * * * *", # chạy mỗi 30 phút\
    # schedule_interval="@hourly", # chạy mỗi giờ
    # schedule_interval="0,30 * * * *", # chạy vào phút 0 và 30 của mỗi giờ
    schedule_interval="0,10,20,30,40,50 * * * *", # chạy vào phút 0, 10, 20, 30, 40, 50 của mỗi giờ
    catchup=False, # không chạy lại quá khứ
) as dag:

    # Task 1: Kéo dữ liệu và lưu local
    fetch_task = PythonOperator( # tạo task để chạy function fetch_crypto
        task_id="fetch_crypto", # tên task (hàm def đã tạo)
        python_callable=fetch_crypto,
    )

    # tạo task:
    # tên: fetch_crypto
    #chạy function fetch_crypto

    # THIẾT LẬP LUỒNG CHẠY (Thứ tự thực thi)
    fetch_task