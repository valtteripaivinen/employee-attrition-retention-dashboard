# Databricks notebook source
# MAGIC %md
# MAGIC # HR Analytics & Attrition Dashboard — 03 Quality Checks and SQL Analysis
# MAGIC
# MAGIC This notebook validates the complete HR analytics model and runs the main aggregate SQL analyses for the portfolio project.

# COMMAND ----------

import re

from pyspark.sql import functions as F
from pyspark.sql import types as T


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
DRIVER_TABLE = f"{CATALOG}.{SCHEMA}.gold_hr_attrition_drivers"

silver_df = spark.table(SILVER_TABLE)
gold_df = spark.table(GOLD_TABLE)
driver_df = spark.table(DRIVER_TABLE)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Run data-quality checks

# COMMAND ----------

check_rows = []


def add_check(check_name: str, failed_rows: int, expectation: str, where_to_fix: str) -> None:
    check_rows.append(
        (
            check_name,
            "PASS" if failed_rows == 0 else "FAIL",
            int(failed_rows),
            expectation,
            where_to_fix,
        )
    )


silver_count = silver_df.count()
gold_count = gold_df.count()

add_check(
    "Source row count equals 1,470",
    abs(silver_count - 1470),
    "The downloaded Kaggle source contains 1,470 fictional employee rows",
    "01_load_and_clean",
)
add_check(
    "Silver and Gold row counts match",
    abs(silver_count - gold_count),
    "Feature engineering must not add or remove employees",
    "02_feature_engineering_and_metrics",
)

required_columns = [
    "employee_number", "age", "attrition", "department", "job_role",
    "business_travel", "over_time", "monthly_income", "job_satisfaction",
    "environment_satisfaction", "work_life_balance", "years_at_company",
]

null_condition = None
for column in required_columns:
    condition = F.col(column).isNull()
    null_condition = condition if null_condition is None else (null_condition | condition)

add_check(
    "Required fields are populated",
    silver_df.filter(null_condition).count(),
    "No required analytical field is null",
    "01_load_and_clean",
)

add_check(
    "Employee numbers are unique",
    silver_count - silver_df.select("employee_number").distinct().count(),
    "Each employee_number must identify one fictional employee row",
    "Source CSV or 01_load_and_clean",
)

source_business_columns = [
    column for column in silver_df.columns if column not in {"source_file", "loaded_at"}
]
duplicate_rows = silver_count - silver_df.select(*source_business_columns).dropDuplicates().count()
add_check(
    "No exact duplicate employee rows",
    duplicate_rows,
    "The source business columns must not contain exact duplicate rows",
    "Source CSV or 01_load_and_clean",
)

add_check(
    "Attrition values are valid",
    silver_df.filter(~F.col("attrition").isin("Yes", "No") | F.col("attrition").isNull()).count(),
    "Attrition must be Yes or No",
    "01_load_and_clean",
)
add_check(
    "Overtime values are valid",
    silver_df.filter(~F.col("over_time").isin("Yes", "No") | F.col("over_time").isNull()).count(),
    "OverTime must be Yes or No",
    "01_load_and_clean",
)
add_check(
    "Satisfaction scales are between 1 and 4",
    silver_df.filter(
        ~F.col("environment_satisfaction").between(1, 4)
        | ~F.col("job_satisfaction").between(1, 4)
        | ~F.col("relationship_satisfaction").between(1, 4)
        | ~F.col("work_life_balance").between(1, 4)
        | ~F.col("job_involvement").between(1, 4)
    ).count(),
    "All survey rating fields must fall within their documented 1–4 scale",
    "Source CSV or 01_load_and_clean",
)
add_check(
    "Performance rating is 3 or 4",
    silver_df.filter(~F.col("performance_rating").isin(3, 4)).count(),
    "The source uses only performance ratings 3 and 4",
    "Source CSV or 01_load_and_clean",
)
add_check(
    "Numeric workforce values are non-negative",
    silver_df.filter(
        (F.col("age") < 0)
        | (F.col("distance_from_home") < 0)
        | (F.col("monthly_income") < 0)
        | (F.col("total_working_years") < 0)
        | (F.col("years_at_company") < 0)
        | (F.col("years_in_current_role") < 0)
        | (F.col("years_since_last_promotion") < 0)
        | (F.col("years_with_curr_manager") < 0)
    ).count(),
    "Age, distance, income, and experience values cannot be negative",
    "Source CSV or 01_load_and_clean",
)
add_check(
    "Company tenure does not exceed total experience",
    silver_df.filter(F.col("years_at_company") > F.col("total_working_years")).count(),
    "YearsAtCompany must be less than or equal to TotalWorkingYears",
    "Source CSV",
)
add_check(
    "Role and career durations fit within company tenure",
    silver_df.filter(
        (F.col("years_in_current_role") > F.col("years_at_company"))
        | (F.col("years_since_last_promotion") > F.col("years_at_company"))
        | (F.col("years_with_curr_manager") > F.col("years_at_company"))
    ).count(),
    "Role, promotion, and manager durations must not exceed company tenure",
    "Source CSV",
)
add_check(
    "Source constant fields match documentation",
    silver_df.filter(
        (F.col("employee_count") != 1)
        | (F.col("over18") != "Y")
        | (F.col("standard_hours") != 80)
    ).count(),
    "EmployeeCount=1, Over18=Y, and StandardHours=80 for all source rows",
    "Source CSV or 01_load_and_clean",
)

source_attritions = silver_df.filter(F.col("attrition") == "Yes").count()
add_check(
    "Source attrition count equals 237",
    abs(source_attritions - 237),
    "The original source contains 237 Yes values in Attrition",
    "Source CSV or 01_load_and_clean",
)
add_check(
    "Descriptive factor count is between 0 and 7",
    gold_df.filter(~F.col("descriptive_factor_count").between(0, 7)).count(),
    "Seven transparent binary conditions are included in the indicator",
    "02_feature_engineering_and_metrics",
)
add_check(
    "Risk indicator is explicitly non-predictive",
    gold_df.filter(F.col("descriptive_indicator_is_predictive") != F.lit(False)).count(),
    "The portfolio indicator must never be labelled as a predictive model",
    "02_feature_engineering_and_metrics",
)
add_check(
    "Driver benchmark table was created",
    0 if driver_df.count() > 0 else 1,
    "At least one aggregate driver row must exist",
    "02_feature_engineering_and_metrics",
)

check_schema = T.StructType([
    T.StructField("check_name", T.StringType(), False),
    T.StructField("status", T.StringType(), False),
    T.StructField("failed_rows_or_delta", T.LongType(), False),
    T.StructField("expectation", T.StringType(), False),
    T.StructField("where_to_fix", T.StringType(), False),
])

checks_df = spark.createDataFrame(check_rows, check_schema)
overall_status = "PASS" if checks_df.filter(F.col("status") == "FAIL").count() == 0 else "FAIL"

(
    checks_df
    .withColumn("model_status", F.lit(overall_status))
    .withColumn("checked_at", F.current_timestamp())
    .write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.hr_data_quality_checks")
)

print(f"MODEL STATUS: {overall_status}")
display(checks_df.orderBy(F.col("status").asc(), F.col("check_name")))

if overall_status == "FAIL":
    raise AssertionError("One or more data-quality checks failed. Review the displayed checks before continuing.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Executive workforce KPIs

# COMMAND ----------

display(spark.sql(f"""
SELECT
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    SUM(retained_flag) AS retained_employees,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(age), 2) AS average_age,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(years_at_company), 2) AS average_years_at_company,
    ROUND(AVG(job_satisfaction), 2) AS average_job_satisfaction,
    ROUND(AVG(work_life_balance), 2) AS average_work_life_balance
FROM {GOLD_TABLE}
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Department analysis

# COMMAND ----------

display(spark.sql(f"""
SELECT
    department,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(job_satisfaction), 2) AS average_job_satisfaction,
    ROUND(AVG(CASE WHEN over_time = 'Yes' THEN 1 ELSE 0 END), 4) AS overtime_rate
FROM {GOLD_TABLE}
GROUP BY department
ORDER BY attrition_rate DESC
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. Job-role analysis

# COMMAND ----------

display(spark.sql(f"""
SELECT
    job_role,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(years_at_company), 2) AS average_years_at_company
FROM {GOLD_TABLE}
GROUP BY job_role
ORDER BY attrition_rate DESC
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5. Overtime and business-travel association

# COMMAND ----------

display(spark.sql(f"""
SELECT
    over_time,
    business_travel,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income
FROM {GOLD_TABLE}
GROUP BY over_time, business_travel
ORDER BY attrition_rate DESC
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 6. Age and tenure cohorts

# COMMAND ----------

display(spark.sql(f"""
SELECT
    age_band,
    tenure_band,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income
FROM {GOLD_TABLE}
GROUP BY age_band, tenure_band
ORDER BY age_band, tenure_band
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 7. Compensation and career progression
# MAGIC
# MAGIC `MonthlyIncome` is shown in the source's unspecified units. Do not add a currency symbol unless the source is replaced with data whose currency is known.

# COMMAND ----------

display(spark.sql(f"""
SELECT
    job_level,
    income_band,
    COUNT(DISTINCT employee_number) AS headcount,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(percent_salary_hike), 2) AS average_salary_hike_pct,
    ROUND(AVG(years_since_last_promotion), 2) AS average_years_since_promotion,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate
FROM {GOLD_TABLE}
GROUP BY job_level, income_band
ORDER BY job_level, income_band
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 8. Employee-experience ratings

# COMMAND ----------

display(spark.sql(f"""
SELECT
    job_satisfaction_label,
    work_life_balance_label,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(environment_satisfaction), 2) AS average_environment_satisfaction,
    ROUND(AVG(job_involvement), 2) AS average_job_involvement
FROM {GOLD_TABLE}
GROUP BY job_satisfaction_label, work_life_balance_label
ORDER BY job_satisfaction_label, work_life_balance_label
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 9. Distance and stock-option analysis

# COMMAND ----------

display(spark.sql(f"""
SELECT
    distance_band,
    stock_option_level,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income
FROM {GOLD_TABLE}
GROUP BY distance_band, stock_option_level
ORDER BY attrition_rate DESC
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 10. Descriptive factor bands
# MAGIC
# MAGIC This analysis is an aggregate prioritization view, not an individual prediction or employment decision tool.

# COMMAND ----------

display(spark.sql(f"""
SELECT
    descriptive_factor_band,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS observed_attritions,
    ROUND(AVG(attrition_flag), 4) AS observed_attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(job_satisfaction), 2) AS average_job_satisfaction,
    ROUND(AVG(work_life_balance), 2) AS average_work_life_balance
FROM {GOLD_TABLE}
GROUP BY descriptive_factor_band
ORDER BY descriptive_factor_band
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 11. Highest aggregate attrition lifts
# MAGIC
# MAGIC Sensitive attributes such as gender may be monitored for fairness and context, but should not be used to target individual employment actions.

# COMMAND ----------

display(spark.sql(f"""
SELECT
    dimension,
    category,
    headcount,
    attritions,
    ROUND(attrition_rate, 4) AS attrition_rate,
    ROUND(attrition_lift, 2) AS attrition_lift
FROM {DRIVER_TABLE}
WHERE headcount >= 25
ORDER BY attrition_lift DESC, headcount DESC
"""))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 12. Final source reconciliation

# COMMAND ----------

reconciliation = silver_df.agg(
    F.count("*").alias("employee_rows"),
    F.countDistinct("employee_number").alias("unique_employee_numbers"),
    F.sum(F.when(F.col("attrition") == "Yes", 1).otherwise(0)).alias("attritions"),
    F.sum(F.when(F.col("attrition") == "No", 1).otherwise(0)).alias("retained_employees"),
    F.round(F.avg("age"), 2).alias("average_age"),
    F.round(F.avg("monthly_income"), 2).alias("average_monthly_income"),
)

display(reconciliation)

