# Databricks notebook source
# MAGIC %md
# MAGIC # HR Analytics & Attrition Dashboard — 04 Export for Power BI
# MAGIC
# MAGIC Run this notebook only after notebooks 01–03 complete successfully. It creates four clean CSV files in a Unity Catalog volume.

# COMMAND ----------

import re

from pyspark.sql import functions as F


def validate_identifier(value: str, label: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


dbutils.widgets.text("catalog", "workspace", "1. Catalog")
dbutils.widgets.text("schema", "hr_portfolio", "2. Schema")
dbutils.widgets.text("export_volume", "power_bi_exports", "3. Export volume")

CATALOG = validate_identifier(dbutils.widgets.get("catalog").strip(), "catalog")
SCHEMA = validate_identifier(dbutils.widgets.get("schema").strip(), "schema")
EXPORT_VOLUME = validate_identifier(dbutils.widgets.get("export_volume").strip(), "export volume")

FULL_SCHEMA = f"`{CATALOG}`.`{SCHEMA}`"
EXPORT_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{EXPORT_VOLUME}"

spark.sql(f"CREATE VOLUME IF NOT EXISTS {FULL_SCHEMA}.`{EXPORT_VOLUME}`")

quality_df = spark.table(f"{CATALOG}.{SCHEMA}.hr_data_quality_checks")
failed_checks = quality_df.filter(F.col("status") == "FAIL").count()

if failed_checks:
    raise AssertionError("Export stopped because one or more data-quality checks failed.")

print(f"Export destination: {EXPORT_PATH}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Export one clearly named CSV per analytical table

# COMMAND ----------


def export_one_csv(dataframe, file_stem: str) -> str:
    if not re.fullmatch(r"[a-z0-9_]+", file_stem):
        raise ValueError(f"Unsafe file stem: {file_stem!r}")

    temporary_path = f"{EXPORT_PATH}/_{file_stem}_temporary"
    final_path = f"{EXPORT_PATH}/{file_stem}.csv"

    dbutils.fs.rm(temporary_path, recurse=True)
    (
        dataframe
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .csv(temporary_path)
    )

    part_files = [
        item.path
        for item in dbutils.fs.ls(temporary_path)
        if item.name.startswith("part-") and item.name.endswith(".csv")
    ]

    if len(part_files) != 1:
        raise RuntimeError(f"Expected one CSV part file, found: {part_files}")

    dbutils.fs.rm(final_path, recurse=False)
    dbutils.fs.cp(part_files[0], final_path)
    dbutils.fs.rm(temporary_path, recurse=True)
    return final_path


employee_export_df = (
    spark.table(f"{CATALOG}.{SCHEMA}.gold_hr_employee_analytics")
    .drop(
        "employee_count", "over18", "standard_hours", "source_file", "loaded_at",
    )
)

exports = [
    (employee_export_df, "hr_employee_analytics"),
    (spark.table(f"{CATALOG}.{SCHEMA}.gold_hr_attrition_drivers"), "hr_attrition_drivers"),
    (spark.table(f"{CATALOG}.{SCHEMA}.gold_hr_department_summary"), "hr_department_summary"),
    (spark.table(f"{CATALOG}.{SCHEMA}.gold_hr_job_role_summary"), "hr_job_role_summary"),
]

created_files = []
for dataframe, file_stem in exports:
    created_files.append(export_one_csv(dataframe, file_stem))

print("CSV exports created:")
for path in created_files:
    print(f"- {path}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Preview exported files

# COMMAND ----------

display(dbutils.fs.ls(EXPORT_PATH))

