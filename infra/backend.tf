# TODO:
# Configure remote Terraform state after AWS setup is complete.
#
# Planned backend:
# - S3 bucket for Terraform state
# - DynamoDB table for state locking
#
# Example:
#
# terraform {
#   backend "s3" {
#     bucket         = "replace with terraform state file"
#     key            = "replace with state file location (dev/terraform.tfstate)"
#     region         = "us-east-1"
#     dynamodb_table = "replace with state locks"
#     encrypt        = true
#   }
# }