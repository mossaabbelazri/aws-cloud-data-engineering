provider "aws" {
  region = "us-east-1"
}

# --- VARIABLES ---
variable "project_name" {
  default = "ytda-automation"
}

variable "alert_email" {
  # Mets ton adresse e-mail ici pour recevoir la notification de succès
  default = "belazrimossaab@gmail.com"
}

# --- S3 BUCKETS ---
resource "aws_s3_bucket" "raw" {
  bucket = "${var.project_name}-raw-mb-2026"
}

resource "aws_s3_bucket" "processed" {
  bucket = "${var.project_name}-processed-mb-2026"
}

# --- SNS TOPIC ---
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# --- IAM ROLES ---
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_admin" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess" # Simplifié pour le lab, à restreindre en prod
}

# --- LAMBDAS ---
data "archive_file" "crawler_zip" {
  type        = "zip"
  source_file = "trigger_crawler.py"
  output_path = "trigger_crawler.zip"
}

resource "aws_lambda_function" "lambda_crawler" {
  filename         = "trigger_crawler.zip"
  function_name    = "${var.project_name}-trigger-crawler"
  role             = aws_iam_role.lambda_role.arn
  handler          = "trigger_crawler.lambda_handler"
  runtime          = "python3.10" # Version récente et supportée !
  source_code_hash = data.archive_file.crawler_zip.output_base64sha256

  environment {
    variables = { CRAWLER_NAME = "${var.project_name}-crawler" }
  }
}

data "archive_file" "etl_zip" {
  type        = "zip"
  source_file = "trigger_etl.py"
  output_path = "trigger_etl.zip"
}

resource "aws_lambda_function" "lambda_etl" {
  filename         = "trigger_etl.zip"
  function_name    = "${var.project_name}-trigger-etl"
  role             = aws_iam_role.lambda_role.arn
  handler          = "trigger_etl.lambda_handler"
  runtime          = "python3.10"
  source_code_hash = data.archive_file.etl_zip.output_base64sha256

  environment {
    variables = { JOB_NAME = "${var.project_name}-job" } # À remplacer par le nom exact de ton Job Glue si déjà créé
  }
}

# --- TRIGGER S3 -> LAMBDA 1 ---
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_crawler.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.raw.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_crawler.arn
    events              = ["s3:ObjectCreated:*"]
  }
  depends_on = [aws_lambda_permission.allow_s3]
}

# --- EVENTBRIDGE: CRAWLER -> LAMBDA 2 ---
resource "aws_cloudwatch_event_rule" "crawler_success" {
  name        = "${var.project_name}-crawler-success"
  description = "Declenche ETL quand le crawler termine"
  event_pattern = jsonencode({
    source      = ["aws.glue"]
    "detail-type" = ["Glue Crawler State Change"]
    detail      = { crawlerName = ["${var.project_name}-crawler"], state = ["Succeeded"] }
  })
}

resource "aws_cloudwatch_event_target" "run_etl" {
  rule      = aws_cloudwatch_event_rule.crawler_success.name
  target_id = "TriggerETL"
  arn       = aws_lambda_function.lambda_etl.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_etl.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.crawler_success.arn
}

# --- EVENTBRIDGE: ETL -> SNS ---
resource "aws_cloudwatch_event_rule" "etl_success" {
  name        = "${var.project_name}-etl-success"
  description = "Envoie un email quand le Job ETL termine"
  event_pattern = jsonencode({
    source      = ["aws.glue"]
    "detail-type" = ["Glue Job State Change"]
    detail      = { jobName = ["${var.project_name}-job"], state = ["SUCCEEDED"] }
  })
}

resource "aws_cloudwatch_event_target" "send_email" {
  rule      = aws_cloudwatch_event_rule.etl_success.name
  target_id = "SendSNSAlert"
  arn       = aws_sns_topic.alerts.arn
}

resource "aws_sns_topic_policy" "allow_eventbridge" {
  arn    = aws_sns_topic.alerts.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action = "sns:Publish"
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}