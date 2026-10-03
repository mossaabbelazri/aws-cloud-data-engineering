# ☁️ AWS Cloud Data Engineering Bootcamp (Orange Formation)

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)
![Apache Spark](https://img.shields.io/badge/apache_spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

This repository contains the architecture, Infrastructure as Code (IaC), and ETL scripts developed during an intensive Cloud Data Engineering bootcamp hosted by **Orange**. The repository is split into two distinct projects demonstrating both Medallion Architecture Data Lakes and 100% Automated Event-Driven Pipelines.

---

## 📂 Project 1: YouTube Data Lake (Medallion Architecture)
**Directory:** `/YouTube_DataLake`

**Objective:** Clean, transform, and join massive structured (CSV) and semi-structured (JSON) datasets using a classic Big Data architecture.

### 🏗️ Architecture Workflow
1. **Amazon S3 Storage Zones**: Data is ingested into `raw` (Bronze), processed into `cleansed` (Silver), and joined into `analytics` (Gold).
2. **AWS Lambda (Pandas/Data Wrangler)**: An event-driven Lambda function detects incoming YouTube Category JSON files in the `raw` zone, converts them to Parquet format, and pushes them to `cleansed`.
3. **AWS Glue ETL (Spark Job 1)**: Ingests massive YouTube video CSV files, performs schema casting (e.g., text to bigint for views/likes), applies predicate pushdown to ignore corrupt files, partitions the data by region, and saves it as Parquet in the `cleansed` zone.
4. **AWS Glue ETL (Spark Job 2)**: Performs a distributed Spark `JOIN` between the cleaned Video Parquet files and Category Parquet files on `category_id`, saving the finalized analytical dataset into the `analytics` zone.
5. **Amazon Athena**: Serverless SQL querying directly on the `analytics` Gold zone.

---

## 📂 Project 2: Green Taxi Automated Pipeline (Event-Driven & Terraform)
**Directory:** `/GreenTaxi_Pipeline`

**Objective:** Build a 100% automated Event-Driven ETL pipeline deployed entirely through Infrastructure as Code (IaC).

### 🏗️ Architecture Workflow
1. **Terraform (IaC)**: Deployment of S3 buckets (raw/processed), IAM roles, Lambda functions, SNS topics, and Amazon EventBridge rules replacing legacy CloudFormation templates.
2. **EventBridge & Lambda**: When a new CSV (e.g., `2020_Green_Taxi_Trip_Data.csv`) is uploaded, EventBridge triggers a Lambda function (`trigger_crawler.py`) to start data cataloging.
3. **AWS Glue Crawler**: Automatically scans the raw S3 bucket and infers the data schema to create a virtual table in the Glue Data Catalog.
4. **AWS Glue ETL (Spark)**: A second Lambda (`trigger_etl.py`) starts the Spark job, which transforms date columns (`lpep_pickup_datetime`) from strings to timestamps, drops empty columns (`ehail_fee`), and converts the dataset to Parquet to optimize Athena querying costs.
5. **Amazon SNS**: Sends email alerts upon successful pipeline completion.

---

## 🛠️ Repository Structure

```bash
.
├── YouTube_DataLake/
│   ├── lambda_json_to_parquet.py    # Triggered on JSON upload
│   ├── glue_job1_clean_csv.py       # Cleans massive CSVs & partitions
│   └── glue_job2_join_data.py       # Spark JOIN on Video and Category data
│
├── GreenTaxi_Pipeline/
│   ├── main.tf                      # Terraform infrastructure deployment
│   ├── trigger_crawler.py           # Lambda: Starts Glue Crawler
│   ├── trigger_etl.py               # Lambda: Starts Glue ETL Job
│   └── glue_taxi_etl.py             # Spark job: Type casting & cleaning
│
├── .gitignore                       
└── README.md
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
