import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 1. Load Cleansed Videos (Parquet)
videos_node = glueContext.create_dynamic_frame.from_catalog(
    database="youtube_db", 
    table_name="cleansed_videos"
)

# 2. Load Cleansed Categories (Parquet)
categories_node = glueContext.create_dynamic_frame.from_catalog(
    database="youtube_db", 
    table_name="cleansed_categories"
)

# 3. Join Videos and Categories on category_id
join_node = Join.apply(
    frame1=videos_node, 
    frame2=categories_node, 
    keys1=["category_id"], 
    keys2=["id"], 
    transformation_ctx="join_node"
)

# 4. Write to Analytics (Gold)
datasink = glueContext.write_dynamic_frame.from_options(
    frame=join_node,
    connection_type="s3",
    connection_options={"path": "s3://my-datalake/analytics/youtube_final/"},
    format="parquet"
)

job.commit()
