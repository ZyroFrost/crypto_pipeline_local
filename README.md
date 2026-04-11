# Crypto Data Pipeline (End-to-End ETL)

> 🚀 **Live Web UI / Demo:** [http://crypto-data-pipeline.duckdns.org/](http://crypto-data-pipeline.duckdns.org/)
> 
> 🔑 **Guest Account (Read-only):** `account: guest` / `password: guest`

## Overview
This project is an automated ETL pipeline for cryptocurrency data. Instead of using a paid Cloud VM, this version utilizes **WSL2 (Windows Subsystem for Linux)** and **Docker Desktop** to host a self-managed local production environment. The pipeline extracts data from APIs, processes it locally using Apache Airflow, and loads the structured data into a **Google Cloud Storage (GCS)** Data Lake and **BigQuery** Data Warehouse. The pipeline is fully containerized and accessible via a custom DuckDNS domain.

## Architecture & Tech Stack
* **Local Environment:** WSL2 (Ubuntu 22.04 LTS) running on Windows.
* **Storage (Data Lake):** Google Cloud Storage (GCS) with Hive Partitioning.
* **Data Warehouse:** Google BigQuery.
* **Orchestration:** Apache Airflow (LocalExecutor) running on Docker.
* **Database:** PostgreSQL (Airflow Metadata).
* **Networking:** DuckDNS (Free Dynamic DNS).
* **Development:** VS Code (WSL Extension).

---

## Complete Setup Guide (From Scratch)

### Phase 1: Local Environment Provisioning (WSL2 & Docker)

**1. Enable WSL2 and Install Ubuntu**
* **Purpose:** To create a native Linux kernel environment on Windows, which is essential for running Dockerized Airflow efficiently.
* Open PowerShell as Administrator and run:
```powershell
wsl --install
```
* Restart your PC. Once finished, a terminal will appear asking you to set up your Ubuntu `username` and `password`.

**2. Configure Docker Desktop**
* **Purpose:** To manage containers across Windows and WSL2 seamlessly.
* Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
* Open Docker Desktop -> Go to **Settings** (gear icon) -> **General** -> Enable **"Use the WSL 2 based engine"**.
* Go to **Resources** -> **WSL Integration** -> Toggle the switch for your **Ubuntu** distribution to ON. Click **Apply & restart**.

**3. Connect using VS Code**
* **Purpose:** To write code and run terminal commands directly inside the Linux subsystem using an integrated development environment (IDE).
* Open VS Code, install the **WSL** extension (by Microsoft).
* Press `Ctrl+Shift+P`, type `WSL: Connect to WSL`, and select it. You are now operating entirely inside your Ubuntu environment.

---

### Phase 2: Google Cloud Platform (GCP) Provisioning

**1. Create a GCS Bucket**
* **Purpose:** To act as our Cloud Data Lake. This is where the pipeline will permanently store the extracted cryptocurrency JSON files for future analytics.
* Go to GCP Console -> **Cloud Storage** -> **Buckets** -> **Create**.
* Name it (e.g., `crypto-pipeline-store`), choose Region, and click Create.

<img width="862" height="439" alt="image" src="https://github.com/user-attachments/assets/6fbd6c5b-6c33-4972-9327-8d7c919b407c" />

---

**2. Set up BigQuery (Data Warehouse)**
* **Purpose:** To create a structured database (Dataset) where your processed crypto data will be stored, allowing you to run SQL queries.
* **Step 1: Create Dataset:**
    * Go to **BigQuery** in the Google Cloud Console.
    * In the **Explorer** panel, click the three vertical dots next to your **Project ID** and select **Create dataset**.
    * **Dataset ID:** Enter a name (e.g., `crypto_data`).
    * **Location type:** Select **Region** and choose the exact same region as your GCS Bucket (to stay in Free Tier).
    * Click **CREATE DATASET**.
* **Step 2: Enable BigQuery API:**
    * Go to **APIs & Services** -> **Library**.
    * Search for **BigQuery API** and ensure it is **Enabled**.
* **Step 3: Table Schema:**
    * You don't need to create tables manually; the Airflow DAG will automatically create them using the `GCSToBigQueryOperator`.

---

**3. Create a Service Account & JSON Key**
* **Purpose:** To provide a secure "ID card" for Airflow. This JSON key authenticates your local WSL2 system, allowing it to securely write data to GCP without needing your personal Google login.
* **Step 1:** Go to **IAM & Admin** -> **Service Accounts** -> Click **+ CREATE SERVICE ACCOUNT**.
* **Step 2:** Enter a name (e.g., `airflow-gcp-zyro`) and click **CREATE AND CONTINUE**.
* **Step 3:** Under "Grant this service account access to project", assign roles based on your deployment strategy:
  * 🚀 **For Quick Testing (Current Setup):** Select **Storage Object Admin** and **BigQuery Admin**. 
    *(Note: This grants full control to bypass permission errors during local development, but is strictly for testing).*
  * 🛡️ **For Production (Best Practice):** Apply the *Principle of Least Privilege* by assigning exactly what the pipeline needs to operate safely: 
    **Storage Object Creator** (to write files to GCS), **BigQuery Data Editor** (to insert data into tables), and **BigQuery Job User** (to execute the load jobs).
  * Choose your preferred roles, click **CONTINUE**, and then **DONE**.
* **Step 4:** In the Service Accounts list, click on the **Email** of the account you just created.
* **Step 5:** Go to the **Keys** tab -> Click **ADD KEY** -> Select **Create new key**.
* **Step 6:** Choose **JSON** as the key type and click **CREATE**.
* **Step 7:** A `.json` file will automatically download to your computer. **This is your only copy of the key.**
* **Step 8:** Move or copy the content of this file to `~/projects/crypto_pipeline/service-account.json` on your WSL/Ubuntu system.

<img width="563" height="602" alt="image" src="https://github.com/user-attachments/assets/d4cdca79-0d3c-4923-b1d1-1ba937e40e70" />
<br>

---
---

### Phase 3: Domain Setup (DuckDNS)

**🚦 Choose your setup path:**
* **👉 For Standard Local Use:** Skip this entire phase. You can access Airflow directly via `http://localhost:8080`.
* **👉 For Remote Access (Recommended):** Follow the steps below to map your Home IP to a free Domain, allowing you to monitor Airflow from anywhere.

**1. Register Domain**
* **Purpose:** To provide a static, easy-to-remember web address (like `my-pipeline.duckdns.org`).
* Go to [DuckDNS.org](https://www.duckdns.org/) and log in.
* In the "domains" section, type a name and click **add domain**.
* Copy your **token** (a long string of characters at the top of the page).

---

**2. Automate IP Update via Cron Job**
* **Purpose:** Home ISP IPs change frequently. By adding a cron job to WSL2, it will automatically update DuckDNS with your latest IP every 5 minutes.
* Open your Ubuntu terminal in VS Code and open the crontab editor:
```bash
crontab -e
```
*(If prompted to choose an editor, press `1` for nano).*
* Scroll to the very bottom of the file and paste this exact line (Replace `<YOUR_DOMAIN>` and `<YOUR_TOKEN>` with your details):
```text
*/5 * * * * curl -k "[https://www.duckdns.org/update?domains=](https://www.duckdns.org/update?domains=)<YOUR_DOMAIN>&token=<YOUR_TOKEN>&ip="
```
* Save the file by pressing `Ctrl + O` -> `Enter`. Then exit by pressing `Ctrl + X`.
<br>

---
---

### Phase 4: Project Setup & Configuration

Open the VS Code integrated terminal (ensure you are connected to WSL).

**1. Clone the Repository**
* **Purpose:** To download the pipeline code (DAGs, configuration) to your WSL environment.
```bash
git clone [https://github.com/ZyroFrost/crypto_pipeline.git](https://github.com/ZyroFrost/crypto_pipeline.git)
cd crypto_pipeline
```

---

**2. Add the GCP Service Account Key**
* **Purpose:** To physically place the authentication key inside the project folder so Docker can mount it into the Airflow container.
* Drag and drop the `.json` file you downloaded in Phase 2 into the `crypto_pipeline` folder in VS Code.
* Rename it EXACTLY to: `service-account.json`.

---

**3. Set Directory Permissions**
* **Purpose:** Docker containers for Airflow run under user ID `50000`. This command grants that specific user permission to read the DAGs and write temporary data to the local disk.
```bash
sudo chown -R 50000:0 .
```
<br>

---
---

### Phase 5: Airflow Deployment

**1. Start the System**
* **Purpose:** To build the custom Airflow image (installing required Python packages) and spin up the Webserver, Scheduler, and Database in detached mode (background).
```bash
docker-compose up -d --build
```

---

**2. Verify**
* **Purpose:** To ensure no containers crashed during startup.
```bash
docker ps
```
Make sure `postgres`, `airflow-scheduler`, and `crypto-airflow` (webserver) are running.

---

## Usage
1. Open your browser and navigate to your DuckDNS domain or localhost:
   * **Local:** `http://localhost:8080/`
   * **Remote:** `http://<your-domain>.duckdns.org:8080/` (Ensure port 8080 is forwarded on your router).
2. Log in with the credentials set in your `.env` or `docker-compose.yml`:
   * **Username:** `admin`
   * **Password:** `<YOUR_SECURE_PASSWORD>`
3. Unpause the `crypto_pipeline` DAG. It will run tasks in this order:
   * **fetch_crypto:** Hits the API, adds execution timestamps, saves JSON locally.
   * **upload_to_gcs:** Pushes the local JSON to the GCS bucket using dynamic XCom pathing and Hive partitioning (`partition_date=YYYY-MM-DD`).
   * **load_to_bigquery:** Automatically infers schema and loads data from GCS into the BigQuery table.
   * **cleanup_local_files:** Deletes the temporary local JSON files to save WSL disk space.

---

## Pipeline in Action (Monitoring)

### 🚀 Airflow Orchestration Dashboard
Showing 25 consecutive successful runs, proving the stability of the local WSL2 production environment.

<img width="1387" height="1034" alt="Airflow Dashboard" src="https://github.com/user-attachments/assets/7e5f78be-0b30-4e0a-bee3-221432efe93d" />

### 🗄️ BigQuery Analytics Ready
Data is automatically partitioned and available for SQL querying.

<img width="558" height="244" alt="BigQuery Table" src="https://github.com/user-attachments/assets/f1335be1-7393-4adb-9bce-6095e2d44eac" />

---

## Maintenance & Troubleshooting
* **View Webserver Logs:**
  ```bash
  docker logs -f crypto-airflow
  ```
* **View Scheduler Logs:**
  ```bash
  docker logs -f airflow-scheduler
  ```
* **Stop Services (Keep Data):**
  ```bash
  docker-compose stop
  ```
* **Wipe Everything (Including Database Volume):**
  ```bash
  docker-compose down -v
  ```
