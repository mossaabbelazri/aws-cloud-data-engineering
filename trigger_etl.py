import boto3
import os

def lambda_handler(event, context):
    glue = boto3.client('glue')
    job_name = os.environ['JOB_NAME']
    print(f"Démarrage du job ETL: {job_name}")
    
    response = glue.start_job_run(JobName=job_name)
    return response