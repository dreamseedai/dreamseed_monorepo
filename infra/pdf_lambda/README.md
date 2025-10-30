# PDF Generator Lambda (AWS SAM, Container Image)

This folder contains a container-based AWS Lambda for PDF/Chart generation with Korean font support, plus a DynamoDB table for job status and an S3 bucket for artifacts.

## What it does
- Accepts job payloads (API Gateway proxy, SQS, or direct invoke)
- Renders a simple chart (matplotlib, Agg backend) and embeds it in a PDF (ReportLab)
- Stores the PDF in S3 and records status in DynamoDB
- Optionally returns a pre‑signed URL

## Structure
- `lambda_function.py` — handler with idempotency, structured logs, SSE, presigned URL option
- `requirements.txt` — Python dependencies
- `Dockerfile` — builds from `public.ecr.aws/lambda/python:3.11` and installs system libs
- `template.yaml` — AWS SAM template (S3 Bucket, DynamoDB Table, Lambda Function)

## Korean font
- Provide a Korean font file (e.g., NotoSansCJK) and copy it into the image:
  - Put your font at `infra/pdf_lambda/fonts/NotoSansCJK-Regular.ttc` and uncomment the COPY/ENV lines in Dockerfile
  - Or set `KOREAN_TTF_PATH` via environment variable and mount/provide the font at that path

## Build & Deploy (SAM CLI)

Prerequisites:
- AWS CLI configured (credentials + region)
- SAM CLI installed
- Docker installed/running

Commands:

```bash
# from repo root
cd infra/pdf_lambda

# Build image and package via SAM
sam build --use-container

# Create a new CloudFormation stack (set a unique stack name)
# The first deploy will prompt for ECR repo creation and parameters (accept defaults)
sam deploy \
  --stack-name seedtest-pdf \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --image-repositories $(aws cloudformation describe-stacks --stack-name seedtest-pdf 2>/dev/null >/dev/null || echo '')
```

Note: On first deploy, SAM will create an ECR repo automatically. If `sam deploy` prompts for parameters, choose sensible defaults. You can later update parameters (e.g., `ReturnPresignedUrl`, `S3Prefix`, `SseMode`, `KmsKeyId`).

## Invoking

- API Gateway → Lambda: send JSON in `body` string
- SQS → Lambda: send JSON in record `body`
- Direct invoke: pass the payload directly

Example test event (API Gateway proxy):
```json
{
  "body": "{\"title\":\"수학 성취 보고서\",\"chart_data\":{\"x\":[0,1,2,3],\"y\":[2,1,3,4],\"title\":\"정답률 추이\"}}"
}
```

## Outputs
After deploy, SAM prints outputs:
- FunctionArn — the Lambda ARN to invoke from your backend
- BucketName — where PDFs are stored
- TableName — where job statuses are tracked

Use these values to configure your FastAPI backend.
