from dotenv import load_dotenv
load_dotenv()
import json
import os
import pathlib
import functions_framework
from google.cloud import storage
from google.cloud import bigquery

# Setup
storage_client = storage.Client()
bq_client = bigquery.Client()
DIRNAME = pathlib.Path(__file__).parent

@functions_framework.http
def generate_assessment_chart_configs(request):
    print('Generating assessment chart config...')

    derived_dataset = os.getenv('DERIVED_DATASET')

    # 1. Query BigQuery
    query = f"""
        SELECT tax_year, lower_bound, upper_bound, property_count
        FROM `{derived_dataset}.tax_year_assessment_bins`
        ORDER BY tax_year, lower_bound
    """
    results = bq_client.query(query).result()
    
    # 2. Transform data into a chart-friendly structure
    chart_data = {}
    for row in results:
        tax_year = str(row.tax_year)
        if tax_year not in chart_data:
            chart_data[tax_year] = []
        chart_data[tax_year].append({
            "lower_bound": float(row.lower_bound),
            "upper_bound": float(row.upper_bound),
            "property_count": int(row.property_count)
        })

    # 3. Write to a local temp file
    prepared_filename = os.path.join("/tmp", "tax_year_assessment_bins.json")
    with open(prepared_filename, "w") as f:
        json.dump(chart_data, f)
    print(f'Wrote config to {prepared_filename}')
    
    # 4. Upload the prepared data to the bucket
    bucket_name = os.getenv('PUBLIC_DATA_BUCKET')
    bucket = storage_client.bucket(bucket_name)
    prepared_blobname = 'configs/tax_year_assessment_bins.json'
    blob = bucket.blob(prepared_blobname)
    blob.upload_from_filename(prepared_filename)
    print(f'Uploaded to {prepared_blobname}')

    return f'Uploaded to gs://{bucket_name}/{prepared_blobname}'

