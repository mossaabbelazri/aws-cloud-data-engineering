import boto3
import os

def lambda_handler(event, context):
    glue = boto3.client('glue')
    crawler_name = os.environ['CRAWLER_NAME']
    print(f"Démarrage du crawler: {crawler_name}")
    
    response = glue.start_crawler(Name=crawler_name)
    return response