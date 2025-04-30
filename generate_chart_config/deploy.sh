#!/usr/bin/env bash
set -euo pipefail

gcloud functions deploy generate-assessment-chart-configs \
  --runtime python310 \
  --trigger-http \
  --entry-point generate_assessment_bins \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BUCKET=musa5090s25-team3-public,\
DEST_PATH=configs/current_assessment_bins.json
