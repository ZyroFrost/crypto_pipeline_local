# declarative workflow (định nghĩa pipeline)
from airflow import DAG
from airflow.operators.python import PythonOperator # operator để chạy function Python

from datetime import datetime, timezone, timedelta

import requests, os, json

GCS_BUCKET_NAME = "zyro-crypto-raw"

# Define DAG
default_args = {
    "owner": "airflow", # name
    "retries": 3, # nếu API fail -> tự retry 3 lần
    "retry_delay": timedelta(minutes=1), # thời gian chờ giữa các lần retry
}

with DAG(
    dag_id="2_crypto_upload", # tên DAG (hiện trên UI)
    start_date=datetime(2024, 1, 1), # mốc bắt đầu
    # schedule_interval="*/30 * * * *", # chạy mỗi 30 phút\
    schedule_interval="@hourly", # chạy mỗi giờ
    # schedule_interval="0,30 * * * *", # chạy vào phút 0 và 30 của mỗi giờ
    # schedule_interval="0,10,20,30,40,50 * * * *", # chạy vào phút 0, 10, 20, 30, 40, 50 của mỗi giờ
    catchup=False, # không chạy lại quá khứ
) as dag:

    # Task 2: Upload file local đó lên GCS
    from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
    upload_to_gcs_task = LocalFilesystemToGCSOperator(
        task_id="upload_to_gcs",
        src="/opt/airflow/data/raw/{{ ds }}/*.json", # {{ ds }} là biến có sẵn của Airflow, trả về ngày chạy (YYYY-MM-DD)
        # Đặt tên file trên GCS theo template ngày tháng của Airflow cho dễ quản lý
        dst="crypto_data/partition_date={{ ds }}/",
        bucket=GCS_BUCKET_NAME,
        gcp_conn_id="google_cloud_default", # Tên connection tạo trên giao diện UI
    )

    # Task 3: Load dữ liệu từ GCS vào BigQuery
    from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
    load_to_bigquery = GCSToBigQueryOperator(
        task_id='load_to_bigquery',
        bucket=GCS_BUCKET_NAME, # Tên bucket GCS
        source_objects=["crypto_data/partition_date={{ ds }}/*.json"], # Lấy TẤT CẢ các file JSON trong TẤT CẢ các thư mục ngày tháng
        destination_project_dataset_table='financial-data-pipeline-492910.crypto_dataset.crypto_prices', # Project-id + dataset name + table name (auto create)
        source_format='NEWLINE_DELIMITED_JSON', # format chuẩn cho API data
        write_disposition='WRITE_APPEND', # Cứ có file mới là nó ghi nối tiếp vào cuối bảng
        autodetect=True, # BigQuery tự động đọc JSON và tạo cột (schema) không cần gõ tay!
        gcp_conn_id='google_cloud_default'
    )

    # Task 4: Xóa file local sau khi đã upload lên GCS để tiết kiệm dung lượng
    from airflow.operators.bash import BashOperator
    cleanup_task = BashOperator(
        task_id="cleanup_local_files",
        bash_command="rm -f /opt/airflow/data/raw/{{ ds }}/*.json",
    )

    # THIẾT LẬP LUỒNG CHẠY (Thứ tự thực thi)
    upload_to_gcs_task >> load_to_bigquery >> cleanup_task