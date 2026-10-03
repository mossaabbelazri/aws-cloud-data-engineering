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

# 1. Read Raw Green Taxi Data
datasource0 = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [args['SOURCE_PATH']]},
    format="csv",
    format_options={"withHeader": True, "separator": ","}
)

# 2. Drop empty 'ehail_fee' column
dropped_ehail = DropFields.apply(
    frame=datasource0,
    paths=["ehail_fee"]
)

# 3. Type Casting (Strings to Timestamps and Doubles)
applymapping1 = ApplyMapping.apply(
    frame=dropped_ehail,
    mappings=[
        ("VendorID", "string", "VendorID", "int"),
        ("lpep_pickup_datetime", "string", "lpep_pickup_datetime", "timestamp"),
        ("lpep_dropoff_datetime", "string", "lpep_dropoff_datetime", "timestamp"),
        ("store_and_fwd_flag", "string", "store_and_fwd_flag", "string"),
        ("RatecodeID", "string", "RatecodeID", "int"),
        ("PULocationID", "string", "PULocationID", "int"),
        ("DOLocationID", "string", "DOLocationID", "int"),
        ("passenger_count", "string", "passenger_count", "int"),
        ("trip_distance", "string", "trip_distance", "double"),
        ("fare_amount", "string", "fare_amount", "double"),
        ("total_amount", "string", "total_amount", "double")
    ]
)

# 4. Write as Parquet
datasink2 = glueContext.write_dynamic_frame.from_options(
    frame=applymapping1,
    connection_type="s3",
    connection_options={"path": args['DEST_PATH']},
    format="parquet"
)

job.commit()
