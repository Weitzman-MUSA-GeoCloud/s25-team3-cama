from dotenv import load_dotenv
load_dotenv()

import os
import pathlib
import functions_framework
from google.cloud import bigquery

DIR_NAME = pathlib.Path(__file__).parent
SQL_DIR_NAME = DIR_NAME / 'sql'


@functions_framework.http
def run_sql(request):
    # Try to get the 'sql' parameter from query or JSON body
    sql_path = SQL_DIR_NAME / request.args.get('sql')

    # Check if the file exists
    if not sql_path.exists() or not sql_path.is_file():
        return f'File {sql_path} not found', 404

    # Read the SQL file
    with open(sql_path, 'r', encoding='utf-8') as sql_file:
        sql_query_template = sql_file.read()
        sql_query = render_template(
            sql_query_template,
            {
                'bucket_name': os.getenv('PREPARE_DATA_BUCKET'),
                'dataset_name': os.getenv('PREPARE_DATA_DATASET'),
                'internal_dataset': os.getenv('INTERNAL_DATASET'),
                'derived_dataset': os.getenv('DERIVED_DATASET')
            }
        )

    # Run the SQL query
    bigquery_client = bigquery.Client()
    bigquery_client.query_and_wait(sql_query)

    print(f'Ran the SQL file {sql_path}')
    return f'Ran the SQL file {sql_path}'


def render_template(sql_query_template, context):
    clean_template = sql_query_template.replace('${', '{')
    return clean_template.format(**context)
