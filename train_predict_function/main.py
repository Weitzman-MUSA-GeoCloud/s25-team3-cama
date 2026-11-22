import functions_framework
import logging
logging.basicConfig(level=logging.INFO)

@functions_framework.http
def train_and_predict(request):
    import pandas as pd
    import numpy as np
    from datetime import datetime
    from google.cloud import bigquery
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import SplineTransformer

    # ─── 1. Initialize BigQuery client ───────────────────────────────────────────────
    client = bigquery.Client(project="musa5090s25-team3")

    # ─── 2. Load data from BigQuery ──────────────────────────────────────────────────
    query = """
    SELECT
      SAFE_CAST(sale_price AS FLOAT64)     AS sale_price,
      SAFE_CAST(market_value AS FLOAT64)   AS market_value,
      SAFE_CAST(number_of_bathrooms AS FLOAT64) AS number_of_bathrooms,
      SAFE_CAST(number_of_bedrooms AS FLOAT64)  AS number_of_bedrooms,
      SAFE_CAST(total_livable_area AS FLOAT64) AS total_livable_area,
      SAFE_CAST(total_area AS FLOAT64)           AS total_area,
      SAFE_CAST(fireplaces AS INT64)             AS fireplaces,
      CAST(year_built AS INT64)                  AS year_built,
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*SZ', sale_date) AS sale_date,
      objectid
    FROM `musa5090s25-team3.core.opa_properties`
    WHERE
      SAFE_CAST(sale_price AS FLOAT64) > 10000.0
      AND SAFE_CAST(market_value AS FLOAT64) > 10000.0
      AND SAFE_CAST(number_of_bathrooms AS FLOAT64) > 0.0
      AND SAFE_CAST(number_of_bedrooms AS FLOAT64) > 0.0
      AND SAFE_CAST(total_livable_area AS FLOAT64) >= 300.0
      AND SAFE_CAST(total_area AS FLOAT64) >= SAFE_CAST(total_livable_area AS FLOAT64)
    """
    job = client.query(query)
    rows = job.result()
    df = pd.DataFrame([dict(row) for row in rows])

    # ─── 3. Clean & engineer features ────────────────────────────────────────────────
    # ensure sale_date is UTC-aware, then compare to now()
    df['sale_date'] = pd.to_datetime(df['sale_date'], utc=True)
    df = df[df['sale_date'] <= pd.Timestamp.utcnow()]
    df['sale_year'] = df['sale_date'].dt.year
    df['years_since_sale'] = pd.Timestamp.utcnow().year - df['sale_year']
    df['log_livable_area'] = np.log(df['total_livable_area'])
    df['building_age'] = pd.Timestamp.utcnow().year - df['year_built']
    df['price_per_sqft'] = df['sale_price'] / df['total_livable_area']
    df['quality_adjusted_area'] = df['total_livable_area'] * 1.1

    # Drop rows with missing values in the columns we’ll use
    keep_cols = [
        'log_livable_area',
        'number_of_bathrooms',
        'number_of_bedrooms',
        'fireplaces',
        'year_built',
        'years_since_sale',
        'building_age',
        'price_per_sqft',
        'quality_adjusted_area'
    ]
    df = df.dropna(subset=keep_cols + ['sale_price', 'objectid'])

    # ─── 4. Prepare design matrix with spline on log_livable_area and year_built ─────
    spl_liv = SplineTransformer(n_knots=4, degree=3)
    X_liv = spl_liv.fit_transform(df[['log_livable_area']])
    liv_cols = spl_liv.get_feature_names_out(['log_livable_area'])

    spl_year = SplineTransformer(n_knots=4, degree=3)
    X_year = spl_year.fit_transform(df[['year_built']])
    year_cols = spl_year.get_feature_names_out(['year_built'])

    # Combine all features
    X = pd.DataFrame(X_liv, columns=liv_cols, index=df.index)
    X[year_cols] = X_year
    for feat in ['number_of_bathrooms', 'number_of_bedrooms', 'fireplaces',
                 'years_since_sale', 'building_age', 'price_per_sqft',
                 'quality_adjusted_area']:
        X[feat] = df[feat].values

    # Target variable
    y = np.log(df['sale_price'])

    # ─── 5. Train linear regression ───────────────────────────────────────────────────
    model = LinearRegression().fit(X, y)

    # ─── 6. Predict on full set ──────────────────────────────────────────────────────
    log_preds = model.predict(X)
    df['predicted_value'] = np.exp(log_preds)
    df['predicted_at'] = datetime.utcnow()
    df['property_id'] = df['objectid']

    # Filter out any negative or zero predictions
    results = df.loc[df['predicted_value'] > 0, ['property_id', 'predicted_value', 'predicted_at']]

    # ─── 7. Upload back to BigQuery ──────────────────────────────────────────────────
    logging.info(f"Uploading {len(results)} rows to derived.current_assessments...")
    logging.info(results.head())

    table_ref = client.dataset("derived").table("current_assessments")
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

    try:
        job = client.load_table_from_dataframe(results, table_ref, job_config=job_config)
        job.result()  # Wait for completion
        logging.info("✅ Predictions uploaded to BigQuery: derived.current_assessments")
    except Exception as e:
        logging.error("❌ Upload failed:", exc_info=e)

    return f"✅ Uploaded {len(results)} predictions to BigQuery.", 200