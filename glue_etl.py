import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SOURCE_PATH', 'DEST_PATH'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 1. Read Raw Data (Bronze Bucket)
datasource0 = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [args['SOURCE_PATH']]},
    format="csv",
    format_options={"withHeader": True, "separator": ","}
)

# 2. Data Cleaning & Transformation
applymapping1 = ApplyMapping.apply(
    frame=datasource0,
    mappings=[
        ("id", "string", "id", "int"),
        ("timestamp", "string", "timestamp", "timestamp"),
        ("amount", "string", "amount", "double"),
        ("status", "string", "status", "string")
    ]
)

# 3. Drop Null Fields
cleaned_data = DropNullFields.apply(frame=applymapping1)

# 4. Write Cleansed Data in Parquet Format (Silver/Gold Bucket)
datasink2 = glueContext.write_dynamic_frame.from_options(
    frame=cleaned_data,
    connection_type="s3",
    connection_options={"path": args['DEST_PATH']},
    format="parquet"
)

job.commit()
