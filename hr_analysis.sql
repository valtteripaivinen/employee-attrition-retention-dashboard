-- HR Analytics & Attrition Dashboard
-- Change the catalog or schema if you used different widget values.

USE CATALOG workspace;
USE SCHEMA hr_portfolio;

-- 1. Executive workforce KPIs
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
FROM gold_hr_employee_analytics;

-- 2. Department analysis
SELECT
    department,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(job_satisfaction), 2) AS average_job_satisfaction,
    ROUND(AVG(CASE WHEN over_time = 'Yes' THEN 1 ELSE 0 END), 4) AS overtime_rate
FROM gold_hr_employee_analytics
GROUP BY department
ORDER BY attrition_rate DESC;

-- 3. Job-role analysis
SELECT
    job_role,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(years_at_company), 2) AS average_years_at_company
FROM gold_hr_employee_analytics
GROUP BY job_role
ORDER BY attrition_rate DESC;

-- 4. Overtime and travel
SELECT
    over_time,
    business_travel,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income
FROM gold_hr_employee_analytics
GROUP BY over_time, business_travel
ORDER BY attrition_rate DESC;

-- 5. Age and tenure cohorts
SELECT
    age_band,
    tenure_band,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income
FROM gold_hr_employee_analytics
GROUP BY age_band, tenure_band
ORDER BY age_band, tenure_band;

-- 6. Employee experience
SELECT
    job_satisfaction_label,
    work_life_balance_label,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(environment_satisfaction), 2) AS average_environment_satisfaction,
    ROUND(AVG(job_involvement), 2) AS average_job_involvement
FROM gold_hr_employee_analytics
GROUP BY job_satisfaction_label, work_life_balance_label
ORDER BY job_satisfaction_label, work_life_balance_label;

-- 7. Compensation and career progression
SELECT
    job_level,
    income_band,
    COUNT(DISTINCT employee_number) AS headcount,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(percent_salary_hike), 2) AS average_salary_hike_pct,
    ROUND(AVG(years_since_last_promotion), 2) AS average_years_since_promotion,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate
FROM gold_hr_employee_analytics
GROUP BY job_level, income_band
ORDER BY job_level, income_band;

-- 8. Distance and stock options
SELECT
    distance_band,
    stock_option_level,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS attritions,
    ROUND(AVG(attrition_flag), 4) AS attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income
FROM gold_hr_employee_analytics
GROUP BY distance_band, stock_option_level
ORDER BY attrition_rate DESC;

-- 9. Descriptive factor bands; aggregate context only, not a prediction
SELECT
    descriptive_factor_band,
    COUNT(DISTINCT employee_number) AS headcount,
    SUM(attrition_flag) AS observed_attritions,
    ROUND(AVG(attrition_flag), 4) AS observed_attrition_rate,
    ROUND(AVG(monthly_income), 2) AS average_monthly_income,
    ROUND(AVG(job_satisfaction), 2) AS average_job_satisfaction,
    ROUND(AVG(work_life_balance), 2) AS average_work_life_balance
FROM gold_hr_employee_analytics
GROUP BY descriptive_factor_band
ORDER BY descriptive_factor_band;

-- 10. Highest aggregate attrition lifts; minimum category size 25
SELECT
    dimension,
    category,
    headcount,
    attritions,
    ROUND(attrition_rate, 4) AS attrition_rate,
    ROUND(attrition_lift, 2) AS attrition_lift
FROM gold_hr_attrition_drivers
WHERE headcount >= 25
ORDER BY attrition_lift DESC, headcount DESC;

-- 11. Data-quality status
SELECT *
FROM hr_data_quality_checks
ORDER BY status, check_name;

