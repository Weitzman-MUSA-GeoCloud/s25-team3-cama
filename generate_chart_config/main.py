import json
from google.cloud import bigquery, storage
import os

# BigQuery client
bq = bigquery.Client()

# GCS client
gcs = storage.Client()
BUCKET = os.getenv("PUBLIC_DATA_BUCKET")
DEST_PATH = "configs/current_assessment_bins.json"

def generate_assessment_chart_configs(request):
    # 1) query your derived table
    sql = """
      SELECT
        tax_year,
        lower_bound,
        upper_bound,
        property_count
      FROM `musa5090s25-team3.derived.current_assessment_bins`
      ORDER BY tax_year, lower_bound
    """
    rows = bq.query(sql).result()

    # 2) convert to list-of-dicts
    out = [
      {
        "tax_year":    row.tax_year,
        "lower_bound": row.lower_bound,
        "upper_bound": row.upper_bound,
        "property_count": row.property_count,
      }
      for row in rows
    ]

    # 3) write JSON to GCS
    bucket = gcs.bucket(BUCKET)
    blob   = bucket.blob(DEST_PATH)
    blob.upload_from_string(json.dumps(out, indent=2), content_type="application/json")
    print(f"Uploaded to gs://{BUCKET}/{DEST_PATH}")

    return f"Wrote {len(out)} records to gs://{BUCKET}/{DEST_PATH}", 200
