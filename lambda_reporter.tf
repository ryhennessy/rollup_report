provider "aws" {
}

variable "bucket_name" {
  default = "lacework-comp-reporting"
  type = string
  description = "The name of the bucket where the reports are stored"
}

variable "lacework_keyid" {
  default = "<Insert Key Here>"
  type = string
  description = "Lacework Key ID"
}

variable "lacework_secretkey" {
  default = "<Insert Secret Key Here>"
  type = string
  description = "Lacework API Secret Key"
}

variable "lacework_baseurl" {
  default = "https://<instancename>.lacework.net"
  type = string
  description = "Lacework Instance"
}

resource "aws_s3_bucket" "lacework_reporter_bucket" {
  bucket = var.bucket_name
  acl    = "private"
}

data "aws_iam_policy_document" "lacework_lambda_policy" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.lacework_reporter_bucket.arn,
      "${aws_s3_bucket.lacework_reporter_bucket.arn}/*",
    ]
  }
}

resource "aws_iam_role" "iam_for_lambda_reporter" {
  name = "lacework_lambda_reporter"
  inline_policy {
     policy = data.aws_iam_policy_document.lacework_lambda_policy.json 
     name = "policy-lacework-reporter"
  }
  assume_role_policy = <<EOF
{
   "Version": "2012-10-17",
   "Statement": [
     {
       "Action": "sts:AssumeRole",
       "Principal": {
       "Service": "lambda.amazonaws.com"
    },
    "Effect": "Allow",
    "Sid": ""
 }
 ]
}
 EOF
}

resource "aws_lambda_function" "lacework_comp_reporter" {
  filename      = "lacework-deployment.zip"
  function_name = "lacework_comp_reporter"
  role          = aws_iam_role.iam_for_lambda_reporter.arn
  handler       = "lambda_function.lambda_handler"
  source_code_hash = filebase64sha256("lacework-deployment.zip")
  runtime = "python3.9"
  timeout = 60
  environment {
    variables = {
      LW_SECRETKEY = var.lacework_secretkey
      LW_KEYID = var.lacework_keyid 
      LW_BASEURL = var.lacework_baseurl 
      LW_BUCKET = aws_s3_bucket.lacework_reporter_bucket.bucket
    }
  }
}

resource "aws_cloudwatch_event_rule" "run_lacework_report" {
  name                = "run-lacework-report"
  description         = "Runs Lacework report collection early every morning"
  schedule_expression = "cron(0 10 * * ? *)"
}

resource "aws_cloudwatch_event_target" "run_lacework_report_function" {
  rule      = aws_cloudwatch_event_rule.run_lacework_report.name
  target_id = "lambda"
  arn       =  aws_lambda_function.lacework_comp_reporter.arn 
}

resource "aws_lambda_permission" "allow_run_lacework_report" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lacework_comp_reporter.function_name 
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.run_lacework_report.arn
}

