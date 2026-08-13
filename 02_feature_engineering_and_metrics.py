# Databricks notebook source
# MAGIC %md
# MAGIC # HR Analytics & Attrition Dashboard — 02 Feature Engineering and Metrics
# MAGIC
# MAGIC This notebook creates business-friendly labels and bands, a transparent descriptive risk-factor indicator, workforce KPIs, driver benchmarking, and department and job-role summary tables.
# MAGIC
# MAGIC **Ethical note:** The risk-factor indicator is a rule-based portfolio demonstration. It is not a validated prediction model and must not be used for individual employment decisions.

# COMMAND ----------

import re

from functools import reduce

from pyspark.sql import functions as F


def validate_identifier(value: str, label: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


dbutils.widgets.text("catalog", "workspace", "1. Catalog")
dbutils.widgets.text("schema", "hr_portfolio", "2. Schema")

CATALOG = validate_identifier(dbutils.widgets.get("catalog").strip(), "catalog")
SCHEMA = validate_identifier(dbutils.widgets.get("schema").strip(), "schema")

SILVER_TABLE = f"{CATALOG}.{SCHEMA}.silver_hr_employees"
GOLD_TABLE = f"{CATALOG}.{SCHEMA}.gold_hr_employee_analytics"

silver_df = spark.table(SILVER_TABLE)
print(f"Rows read from Silver: {silver_df.count():,}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Create business-friendly analytical features

# COMMAND ----------


def four_level_label(column_name: str):
    return (
        F.when(F.col(column_name) == 1, "1. Low")
        .when(F.col(column_name) == 2, "2. Medium")
        .when(F.col(column_name) == 3, "3. High")
        .when(F.col(column_name) == 4, "4. Very High")
    )


gold_df = (
    silver_df
    .withColumn("attrition_flag", F.when(F.col("attrition") == "Yes", 1).otherwise(0))
    .withColumn("retained_flag", F.when(F.col("attrition") == "No", 1).otherwise(0))
    .withColumn(
        "age_band",
        F.when(F.col("age") < 25, "1. Under 25")
        .when(F.col("age") <= 34, "2. 25–34")
        .when(F.col("age") <= 44, "3. 35–44")
        .when(F.col("age") <= 54, "4. 45–54")
        .otherwise("5. 55+"),
    )
    .withColumn(
        "tenure_band",
        F.when(F.col("years_at_company") < 1, "1. Under 1 year")
        .when(F.col("years_at_company") <= 2, "2. 1–2 years")
        .when(F.col("years_at_company") <= 5, "3. 3–5 years")
        .when(F.col("years_at_company") <= 10, "4. 6–10 years")
        .otherwise("5. 11+ years"),
    )
    .withColumn(
        "income_band",
        F.when(F.col("monthly_income") < 3000, "1. Under 3,000")
        .when(F.col("monthly_income") < 5000, "2. 3,000–4,999")
        .when(F.col("monthly_income") < 10000, "3. 5,000–9,999")
        .otherwise("4. 10,000+"),
    )
    .withColumn(
        "distance_band",
        F.when(F.col("distance_from_home") <= 5, "1. 1–5")
        .when(F.col("distance_from_home") <= 10, "2. 6–10")
        .when(F.col("distance_from_home") <= 20, "3. 11–20")
        .otherwise("4. 21+"),
    )
    .withColumn(
        "education_label",
        F.when(F.col("education") == 1, "1. Below College")
        .when(F.col("education") == 2, "2. College")
        .when(F.col("education") == 3, "3. Bachelor")
        .when(F.col("education") == 4, "4. Master")
        .when(F.col("education") == 5, "5. Doctor"),
    )
    .withColumn("environment_satisfaction_label", four_level_label("environment_satisfaction"))
    .withColumn("job_involvement_label", four_level_label("job_involvement"))
    .withColumn("job_satisfaction_label", four_level_label("job_satisfaction"))
    .withColumn("relationship_satisfaction_label", four_level_label("relationship_satisfaction"))
    .withColumn(
        "work_life_balance_label",
        F.when(F.col("work_life_balance") == 1, "1. Poor")
        .when(F.col("work_life_balance") == 2, "2. Fair")
        .when(F.col("work_life_balance") == 3, "3. Good")
        .when(F.col("work_life_balance") == 4, "4. Excellent"),
    )
    .withColumn(
        "performance_rating_label",
        F.when(F.col("performance_rating") == 3, "3. Excellent")
        .when(F.col("performance_rating") == 4, "4. Outstanding"),
    )
    .withColumn(
        "promotion_wait_band",
        F.when(F.col("years_since_last_promotion") == 0, "1. Less than 1 year")
        .when(F.col("years_since_last_promotion") <= 2, "2. 1–2 years")
        .when(F.col("years_since_last_promotion") <= 5, "3. 3–5 years")
        .otherwise("4. 6+ years"),
    )
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Create a transparent descriptive risk-factor indicator
# MAGIC
# MAGIC One point is added for each observable condition below: overtime, frequent business travel, job satisfaction 1–2, work-life balance 1–2, environment satisfaction 1–2, no stock options, and distance from home above 10. The score is descriptive and does not estimate an individual's future behaviour.

# COMMAND ----------

gold_df = (
    gold_df
    .withColumn("factor_overtime", F.when(F.col("over_time") == "Yes", 1).otherwise(0))
    .withColumn("factor_frequent_travel", F.when(F.col("business_travel") == "Travel_Frequently", 1).otherwise(0))
    .withColumn("factor_low_job_satisfaction", F.when(F.col("job_satisfaction") <= 2, 1).otherwise(0))
    .withColumn("factor_poor_work_life_balance", F.when(F.col("work_life_balance") <= 2, 1).otherwise(0))
    .withColumn("factor_low_environment_satisfaction", F.when(F.col("environment_satisfaction") <= 2, 1).otherwise(0))
    .withColumn("factor_no_stock_options", F.when(F.col("stock_option_level") == 0, 1).otherwise(0))
    .withColumn("factor_long_commute", F.when(F.col("distance_from_home") > 10, 1).otherwise(0))
    .withColumn(
        "descriptive_factor_count",
        F.col("factor_overtime")
        + F.col("factor_frequent_travel")
        + F.col("factor_low_job_satisfaction")
        + F.col("factor_poor_work_life_balance")
        + F.col("factor_low_environment_satisfaction")
        + F.col("factor_no_stock_options")
        + F.col("factor_long_commute"),
    )
    .withColumn(
        "descriptive_factor_band",
        F.when(F.col("descriptive_factor_count") <= 2, "1. Low")
        .when(F.col("descriptive_factor_count") <= 4, "2. Moderate")
        .otherwise("3. Elevated"),
    )
    .withColumn("descriptive_indicator_is_predictive", F.lit(False))
)

(
    gold_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(GOLD_TABLE)
)

print(f"Saved employee analytics table: {GOLD_TABLE}")
display(gold_df.orderBy("employee_number").limit(20))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Create workforce KPI summary

# COMMAND ----------

workforce_summary_df = gold_df.agg(
    F.countDistinct("employee_number").alias("headcount"),
    F.sum("attrition_flag").alias("attritions"),
    F.sum("retained_flag").alias("retained_employees"),
    F.avg("attrition_flag").alias("attrition_rate"),
    F.avg("age").alias("average_age"),
    F.avg("monthly_income").alias("average_monthly_income"),
    F.avg("years_at_company").alias("average_years_at_company"),
    F.avg("job_satisfaction").alias("average_job_satisfaction"),
    F.avg("work_life_balance").alias("average_work_life_balance"),
    F.sum(F.when(F.col("over_time") == "Yes", 1).otherwise(0)).alias("overtime_employees"),
)

(
    workforce_summary_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.gold_hr_workforce_summary")
)

display(workforce_summary_df)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. Benchmark attrition drivers
# MAGIC
# MAGIC `attrition_lift` compares each category's attrition rate with the whole fictional workforce. A lift above 1 means the category's observed rate is above the dataset average. Association does not prove causation.

# COMMAND ----------

company_attrition_rate = gold_df.agg(F.avg("attrition_flag").alias("rate")).first()["rate"]

driver_dimensions = [
    ("Department", "department"),
    ("Job Role", "job_role"),
    ("Overtime", "over_time"),
    ("Business Travel", "business_travel"),
    ("Age Band", "age_band"),
    ("Tenure Band", "tenure_band"),
    ("Income Band", "income_band"),
    ("Job Satisfaction", "job_satisfaction_label"),
    ("Work-Life Balance", "work_life_balance_label"),
    ("Environment Satisfaction", "environment_satisfaction_label"),
    ("Stock Option Level", "stock_option_level"),
    ("Distance Band", "distance_band"),
    ("Marital Status", "marital_status"),
    ("Gender", "gender"),
    ("Descriptive Factor Band", "descriptive_factor_band"),
]


def summarize_driver(dimension_name: str, column_name: str):
    return (
        gold_df
        .groupBy(F.col(column_name).cast("string").alias("category"))
        .agg(
            F.countDistinct("employee_number").alias("headcount"),
            F.sum("attrition_flag").alias("attritions"),
            F.avg("attrition_flag").alias("attrition_rate"),
            F.avg("monthly_income").alias("average_monthly_income"),
            F.avg("years_at_company").alias("average_years_at_company"),
            F.avg("job_satisfaction").alias("average_job_satisfaction"),
        )
        .withColumn("dimension", F.lit(dimension_name))
        .withColumn("company_attrition_rate", F.lit(company_attrition_rate))
        .withColumn(
            "attrition_lift",
            F.when(
                F.lit(company_attrition_rate) != 0,
                F.col("attrition_rate") / F.lit(company_attrition_rate),
            ),
        )
        .select(
            "dimension", "category", "headcount", "attritions", "attrition_rate",
            "company_attrition_rate", "attrition_lift", "average_monthly_income",
            "average_years_at_company", "average_job_satisfaction",
        )
    )


driver_frames = [summarize_driver(name, column) for name, column in driver_dimensions]
attrition_drivers_df = reduce(lambda left, right: left.unionByName(right), driver_frames)

(
    attrition_drivers_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.gold_hr_attrition_drivers")
)

display(attrition_drivers_df.orderBy(F.desc("attrition_lift")))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5. Create department and job-role summaries

# COMMAND ----------


def create_org_summary(group_column: str):
    return (
        gold_df
        .groupBy(group_column)
        .agg(
            F.countDistinct("employee_number").alias("headcount"),
            F.sum("attrition_flag").alias("attritions"),
            F.avg("attrition_flag").alias("attrition_rate"),
            F.avg("monthly_income").alias("average_monthly_income"),
            F.avg("age").alias("average_age"),
            F.avg("years_at_company").alias("average_years_at_company"),
            F.avg("job_satisfaction").alias("average_job_satisfaction"),
            F.avg("work_life_balance").alias("average_work_life_balance"),
            F.avg("environment_satisfaction").alias("average_environment_satisfaction"),
            F.sum(F.when(F.col("over_time") == "Yes", 1).otherwise(0)).alias("overtime_employees"),
        )
        .withColumn("overtime_rate", F.col("overtime_employees") / F.col("headcount"))
    )


department_summary_df = create_org_summary("department")
job_role_summary_df = create_org_summary("job_role")

(
    department_summary_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.gold_hr_department_summary")
)

(
    job_role_summary_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.gold_hr_job_role_summary")
)

display(department_summary_df.orderBy(F.desc("attrition_rate")))
display(job_role_summary_df.orderBy(F.desc("attrition_rate")))

