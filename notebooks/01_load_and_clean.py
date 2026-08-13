# Databricks notebook source
# MAGIC %md
# MAGIC # HR Analytics & Attrition Dashboard — 01 Load and Clean
# MAGIC
# MAGIC This notebook creates the project schema and source volume, reads the IBM HR Analytics Employee Attrition & Performance CSV, standardizes column names, validates the source structure, and writes Bronze and Silver Delta tables.
# MAGIC
# MAGIC **Source:** https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset
# MAGIC
# MAGIC **Data note:** This is a fictional dataset created for analytics practice. It does not contain real employee records.

# COMMAND ----------

import re

from pyspark.sql import functions as F


def validate_identifier(value: str, label: str) -> str:
    """Allow only safe Unity Catalog identifiers."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


dbutils.widgets.text("catalog", "workspace", "1. Catalog")
dbutils.widgets.text("schema", "hr_portfolio", "2. Schema")
dbutils.widgets.text("volume", "source_files", "3. Source volume")
dbutils.widgets.text(
    "file_name",
    "WA_Fn-UseC_-HR-Employee-Attrition.csv",
    "4. CSV filename",
)

CATALOG = validate_identifier(dbutils.widgets.get("catalog").strip(), "catalog")
SCHEMA = validate_identifier(dbutils.widgets.get("schema").strip(), "schema")
VOLUME = validate_identifier(dbutils.widgets.get("volume").strip(), "volume")
FILE_NAME = dbutils.widgets.get("file_name").strip()

if not FILE_NAME.lower().endswith(".csv"):
    raise ValueError("file_name must end with .csv")

FULL_SCHEMA = f"`{CATALOG}`.`{SCHEMA}`"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
SOURCE_FILE = f"{VOLUME_PATH}/{FILE_NAME}"

print(f"Project schema: {CATALOG}.{SCHEMA}")
print(f"Upload the CSV file to: {VOLUME_PATH}")
print(f"Expected source file: {SOURCE_FILE}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Create the schema and source volume
# MAGIC
# MAGIC Run this cell once. If the CSV has not been uploaded yet, the expected `FileNotFoundError` confirms that the volume was created and is waiting for the source file.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {FULL_SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {FULL_SCHEMA}.`{VOLUME}`")

available_files = dbutils.fs.ls(VOLUME_PATH)
matching_files = [item.path for item in available_files if item.name == FILE_NAME]

if not matching_files:
    available_names = [item.name for item in available_files]
    raise FileNotFoundError(
        f"Could not find {FILE_NAME!r} in {VOLUME_PATH}. "
        f"Files currently available: {available_names}. "
        "Upload the CSV and run the notebook again."
    )

print(f"Source file found: {matching_files[0]}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Read the CSV as strings
# MAGIC
# MAGIC Reading the raw source as strings preserves the original values in Bronze. Data types are applied deliberately in the Silver step.

# COMMAND ----------

raw_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", False)
    .option("mode", "FAILFAST")
    .option("encoding", "UTF-8")
    .csv(SOURCE_FILE)
)

print(f"Rows loaded: {raw_df.count():,}")
print(f"Columns loaded: {len(raw_df.columns)}")
display(raw_df.limit(10))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Standardize column names and write Bronze

# COMMAND ----------


def to_snake_case(name: str) -> str:
    cleaned = name.replace("\ufeff", "").strip()
    cleaned = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cleaned)
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", cleaned)
    return cleaned.strip("_").lower()


standardized_names = [to_snake_case(column) for column in raw_df.columns]

if len(standardized_names) != len(set(standardized_names)):
    raise ValueError(f"Column-name cleaning produced duplicates: {standardized_names}")

bronze_df = (
    raw_df.toDF(*standardized_names)
    .withColumn("source_file", F.lit(FILE_NAME))
    .withColumn("loaded_at", F.current_timestamp())
)

expected_columns = {
    "age", "attrition", "business_travel", "daily_rate", "department",
    "distance_from_home", "education", "education_field", "employee_count",
    "employee_number", "environment_satisfaction", "gender", "hourly_rate",
    "job_involvement", "job_level", "job_role", "job_satisfaction",
    "marital_status", "monthly_income", "monthly_rate", "num_companies_worked",
    "over18", "over_time", "percent_salary_hike", "performance_rating",
    "relationship_satisfaction", "standard_hours", "stock_option_level",
    "total_working_years", "training_times_last_year", "work_life_balance",
    "years_at_company", "years_in_current_role", "years_since_last_promotion",
    "years_with_curr_manager",
}

missing_columns = sorted(expected_columns - set(bronze_df.columns))
unexpected_columns = sorted(set(bronze_df.columns) - expected_columns - {"source_file", "loaded_at"})

if missing_columns or unexpected_columns:
    raise ValueError(
        f"Source structure mismatch. Missing: {missing_columns}; "
        f"Unexpected: {unexpected_columns}"
    )

(
    bronze_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.bronze_hr_employee_raw")
)

print(f"Saved Bronze table: {CATALOG}.{SCHEMA}.bronze_hr_employee_raw")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. Clean values and apply data types

# COMMAND ----------

text_columns = [
    "attrition", "business_travel", "department", "education_field", "gender",
    "job_role", "marital_status", "over18", "over_time",
]

numeric_columns = [
    "age", "daily_rate", "distance_from_home", "education", "employee_count",
    "employee_number", "environment_satisfaction", "hourly_rate",
    "job_involvement", "job_level", "job_satisfaction", "monthly_income",
    "monthly_rate", "num_companies_worked", "percent_salary_hike",
    "performance_rating", "relationship_satisfaction", "standard_hours",
    "stock_option_level", "total_working_years", "training_times_last_year",
    "work_life_balance", "years_at_company", "years_in_current_role",
    "years_since_last_promotion", "years_with_curr_manager",
]

silver_df = bronze_df

for column in text_columns:
    silver_df = silver_df.withColumn(column, F.trim(F.col(column).cast("string")))

for column in numeric_columns:
    silver_df = silver_df.withColumn(column, F.col(column).cast("int"))

source_order = [
    "age", "attrition", "business_travel", "daily_rate", "department",
    "distance_from_home", "education", "education_field", "employee_count",
    "employee_number", "environment_satisfaction", "gender", "hourly_rate",
    "job_involvement", "job_level", "job_role", "job_satisfaction",
    "marital_status", "monthly_income", "monthly_rate", "num_companies_worked",
    "over18", "over_time", "percent_salary_hike", "performance_rating",
    "relationship_satisfaction", "standard_hours", "stock_option_level",
    "total_working_years", "training_times_last_year", "work_life_balance",
    "years_at_company", "years_in_current_role", "years_since_last_promotion",
    "years_with_curr_manager", "source_file", "loaded_at",
]

silver_df = silver_df.select(*source_order)

(
    silver_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.silver_hr_employees")
)

print(f"Saved Silver table: {CATALOG}.{SCHEMA}.silver_hr_employees")
silver_df.printSchema()
display(silver_df.orderBy("employee_number").limit(20))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5. Basic load summary

# COMMAND ----------

load_summary = silver_df.agg(
    F.count("*").alias("employee_rows"),
    F.countDistinct("employee_number").alias("unique_employee_numbers"),
    F.sum(F.when(F.col("attrition") == "Yes", 1).otherwise(0)).alias("attritions"),
    F.round(F.avg("age"), 2).alias("average_age"),
    F.round(F.avg("monthly_income"), 2).alias("average_monthly_income"),
)

display(load_summary)

