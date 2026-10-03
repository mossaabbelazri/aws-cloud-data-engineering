import pandas as pd
import boto3
import urllib.parse

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Get bucket and file name from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    try:
        # 1. Download JSON from Raw (Bronze)
        response = s3_client.get_object(Bucket=bucket, Key=key)
        json_data = pd.read_json(response['Body'])
        
        # 2. Convert to Parquet using Pandas
        parquet_buffer = json_data.to_parquet(index=False)
        
        # 3. Upload to Cleansed (Silver)
        new_key = key.replace('raw/', 'cleansed/').replace('.json', '.parquet')
        s3_client.put_object(Bucket=bucket, Key=new_key, Body=parquet_buffer)
        
        print(f"Successfully converted {key} to Parquet at {new_key}")
        return {"status": "SUCCESS"}
        
    except Exception as e:
        print(f"Error processing object {key} from bucket {bucket}. Event: {e}")
        raise e
