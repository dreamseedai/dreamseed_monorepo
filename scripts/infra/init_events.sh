#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=${PROJECT_ID:-dreamseedai-prod}
REGION=${REGION:-asia-northeast3}
TEMP_BUCKET="gs://${PROJECT_ID}-dataflow-temp"
SA="seedtest-dataflow@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"

# Pub/Sub topics
gcloud pubsub topics create seedtest-events --message-ordering || true
gcloud pubsub topics create seedtest-events-dlq || true

# GCS bucket for Dataflow temp/staging
gsutil mb -l "$REGION" "$TEMP_BUCKET" || true

# BigQuery dataset
bq --location="$REGION" mk -d ${PROJECT_ID}:seedtest || true

# Service Account IAM
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$SA" --role roles/dataflow.admin || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$SA" --role roles/dataflow.worker || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$SA" --role roles/pubsub.editor || true
gsutil iam ch serviceAccount:$SA:objectAdmin "$TEMP_BUCKET"
bq update --dataset --add_iam_member=WRITER:"serviceAccount:$SA" ${PROJECT_ID}:seedtest || true

echo "✅ Infra ready: $PROJECT_ID ($REGION)"

