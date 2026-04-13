# Crypto Data Pipeline (End-to-End ETL)

## Overview
This project is an automated ETL pipeline for cryptocurrency data. It extracts data from APIs, processes it using Apache Airflow, and loads the structured data into a **Google Cloud Storage (GCS)** Data Lake and **BigQuery** Data Warehouse. 

This repository is designed with two deployment strategies:
1. **🧪 Lab Environment (Local Development):** Utilizes **WSL2** and **Docker Desktop** for local testing, development, and simulating production.
2. **🚀 Production Environment (Cloud Deployment):** Deploys the fully containerized pipeline to a **GCP Compute Engine VM** for stable, continuous execution.

## Architecture & Tech Stack
* **Storage (Data Lake):** Google Cloud Storage (GCS) with Hive Partitioning.
* **Data Warehouse:** Google BigQuery.
* **Orchestration:** Apache Airflow (LocalExecutor) running on Docker.
* **Database:** PostgreSQL (Airflow Metadata).
* **Networking:** DuckDNS (Free Dynamic DNS).
* **Lab Environment:** Windows Subsystem for Linux (WSL2 - Ubuntu 22.04 LTS).
* **Production Environment:** Google Cloud Platform (Compute Engine VM - Debian/Ubuntu).

---

## Phase 1: Common Cloud Setup (GCP & Domain)
*Perform these steps regardless of whether you are deploying to Lab or Production.*

### 1. Create a GCS Bucket (Data Lake)
* Go to GCP Console -> **Cloud Storage** -> **Buckets** -> **Create**.
* Name it (e.g., `crypto-pipeline-store`), choose your Region, and click Create.

<img width="862" height="439" alt="image" src="https://github.com/user-attachments/assets/6fbd6c5b-6c33-4972-9327-8d7c919b407c" />

### 2. Set up BigQuery (Data Warehouse)
* **Create Dataset:** Go to **BigQuery** -> Click the three dots next to your Project ID -> **Create dataset**. Name it `crypto_data`. Ensure the location matches your GCS Bucket to stay in the Free Tier.
* **Enable API:** Go to **APIs & Services** -> **Library** -> Search for **BigQuery API** and ensure it is **Enabled**.
* *(Note: The Airflow DAG will automatically create the required tables using the `GCSToBigQueryOperator`).*

### 3. Create a Service Account & JSON Key
* Go to **IAM & Admin** -> **Service Accounts** -> **+ CREATE SERVICE ACCOUNT**. Name it `airflow-gcp`.
* **Assign Roles:** * 🛡️ **Production (Best Practice):** `Storage Object Creator`, `BigQuery Data Editor`, and `BigQuery Job User`.
  * 🚀 **Quick Testing:** `Storage Object Admin` and `BigQuery Admin`.
* Go to the **Keys** tab -> **ADD KEY** -> **Create new key** -> **JSON**. Download this file; you will need it later.

<img width="563" height="602" alt="image" src="https://github.com/user-attachments/assets/d4cdca79-0d3c-4923-b1d1-1ba937e40e70" />

---

## Phase 2: Deployment Paths
Choose your deployment target below.

### 🧪 PATH A: Lab Environment (Local WSL2)
*Use this for local development and testing.*

**1. Provision WSL2 & Docker**
* Open PowerShell as Admin and run: `wsl --install`. Set up your Ubuntu credentials.
* Install [Docker Desktop](https://www.docker.com/products/docker-desktop/). Enable **"Use the WSL 2 based engine"** in General Settings, and turn on WSL Integration for your Ubuntu distro in Resource Settings.
* Connect to WSL via VS Code using the **WSL** extension.

**2. Automate IP Update (Optional - for remote lab access)**
* Run `crontab -e` and add: 
  `*/5 * * * * curl -k "https://www.duckdns.org/update?domains=<YOUR_DOMAIN>&token=<YOUR_TOKEN>&ip="`

**3. Project Setup**
```bash
git clone [https://github.com/ZyroFrost/crypto_pipeline.git](https://github.com/ZyroFrost/crypto_pipeline.git)
cd crypto_pipeline
# Rename your downloaded GCP key and place it here:
mv /path/to/downloaded/key.json ./service-account.json
sudo chown -R 50000:0 .
docker-compose up -d --build
```

---

### 🚀 PATH B: Production Environment (GCP Compute Engine VM)
*Use this for the final, always-on deployment.*

**1. Provision the VM**
* Go to **Compute Engine** -> **Create Instance**.
* Choose `e2-medium` (Shared core, 4GB RAM), Debian 12 or Ubuntu 22.04 LTS boot disk (10GB).
* Check **Allow HTTP** and **Allow HTTPS traffic**. Note the External Public IP.

<img width="558" height="244" alt="image" src="https://github.com/user-attachments/assets/f1335be1-7393-4adb-9bce-6095e2d44eac" />

**2. Connect via VS Code (Remote-SSH)**
* Generate an SSH key locally: `ssh-keygen -t rsa -b 4096 -C "your_email@example.com"`
* Add the public key (`~/.ssh/id_rsa.pub`) to GCP: **Compute Engine** -> **Metadata** -> **SSH Keys**.
* In VS Code, use the **Remote - SSH** extension and configure your host with the VM's External IP.

**3. Project Setup & Docker Installation**
```bash
# Install Docker
sudo apt update && sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER

# Setup Project
git clone [https://github.com/ZyroFrost/crypto_pipeline.git](https://github.com/ZyroFrost/crypto_pipeline.git)
cd crypto_pipeline
# Drag and drop your GCP JSON key into VS Code and rename it to 'service-account.json'
sudo chown -R 50000:0 .
docker-compose up -d --build
```

---

## Pipeline Usage & Monitoring

**1. Access the Airflow UI**
* **Lab (Local):** `http://localhost:8080/`
* **Production / Remote Lab:** `http://<your-domain>.duckdns.org:8080/` (or via VM IP).
* Log in with credentials (`admin` / `<YOUR_SECURE_PASSWORD>`).

**2. DAG Execution Flow**
Unpause the `crypto_pipeline` DAG. It executes the following tasks:
1. `fetch_crypto`: Hits the API, adds execution timestamps, and saves JSON locally.
2. `upload_to_gcs`: Pushes the local JSON to the GCS bucket using dynamic XCom pathing and Hive partitioning (`partition_date=YYYY-MM-DD`).
3. `load_to_bigquery`: Automatically infers schema and loads data from GCS into the BigQuery table.
4. `cleanup_local_files`: Deletes temporary local JSON files to save disk space.

### 🚀 Airflow Orchestration Dashboard
Showing consecutive successful runs, proving the stability of the ETL process.

<img width="1626" height="166" alt="image" src="https://github.com/user-attachments/assets/793c40ab-be8c-4997-808e-1df10299e6b1" />
<img width="772" height="416" alt="image" src="https://github.com/user-attachments/assets/79b9671c-efae-49f0-9cbf-c517287ef266" />
<img width="1048" height="449" alt="image" src="https://github.com/user-attachments/assets/7c38764c-8597-465f-9a0d-292115d5ec69" />

### 🗄️ BigQuery Analytics Ready
Data is automatically partitioned and available for SQL querying.

---

## Maintenance & Troubleshooting

Run these commands in your project directory (WSL or VM):

| Action | Command |
| :--- | :--- |
| **View Webserver Logs** | `docker logs -f crypto-airflow` |
| **View Scheduler Logs** | `docker logs -f airflow-scheduler` |
| **Check Container Status** | `docker ps` |
| **Stop Services (Keep Data)**| `docker-compose stop` |
| **Wipe Everything (Hard Reset)**| `docker-compose down -v` |
