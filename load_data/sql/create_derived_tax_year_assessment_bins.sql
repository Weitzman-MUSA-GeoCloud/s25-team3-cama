CREATE OR REPLACE TABLE `${derived_dataset}.tax_year_assessment_bins` AS
WITH binned AS (
  SELECT
    year AS tax_year,
    FLOOR(CAST(market_value AS NUMERIC) / 100000) * 100000 AS lower_bound,
    FLOOR(CAST(market_value AS NUMERIC) / 100000) * 100000 + 100000 AS upper_bound
  FROM `${internal_dataset}.opa_assessments`
  WHERE market_value IS NOT NULL
),
aggregated AS (
  SELECT
    tax_year,
    lower_bound,
    upper_bound,
    COUNT(*) AS property_count
  FROM binned
  GROUP BY tax_year, lower_bound, upper_bound
)
SELECT * FROM aggregated
ORDER BY tax_year, lower_bound;
