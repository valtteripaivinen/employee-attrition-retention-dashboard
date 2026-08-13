# HR data dictionary

## Core fields

| Field | Meaning |
|---|---|
| `employee_number` | Unique identifier in the fictional dataset |
| `attrition` | Whether the fictional employee left: Yes or No |
| `department` | Human Resources, Research & Development, or Sales |
| `job_role` | Fictional employee's role |
| `business_travel` | Non-Travel, Travel_Rarely, or Travel_Frequently |
| `over_time` | Whether overtime is recorded: Yes or No |
| `monthly_income` | Monthly income in unspecified source units |
| `distance_from_home` | Distance from home in unspecified source units |
| `years_at_company` | Years at the organization |
| `years_in_current_role` | Years in the current role |
| `years_since_last_promotion` | Years since the latest promotion |
| `years_with_curr_manager` | Years with the current manager |

## Rating scales

| Field | Scale |
|---|---|
| `education` | 1 Below College, 2 College, 3 Bachelor, 4 Master, 5 Doctor |
| `environment_satisfaction` | 1 Low, 2 Medium, 3 High, 4 Very High |
| `job_involvement` | 1 Low, 2 Medium, 3 High, 4 Very High |
| `job_satisfaction` | 1 Low, 2 Medium, 3 High, 4 Very High |
| `relationship_satisfaction` | 1 Low, 2 Medium, 3 High, 4 Very High |
| `work_life_balance` | 1 Poor, 2 Fair, 3 Good, 4 Excellent |
| `performance_rating` | 3 Excellent, 4 Outstanding |

## Constant source fields

`employee_count = 1`, `over18 = Y`, and `standard_hours = 80` for every source row. They are retained in Bronze and Silver for source reconciliation but excluded from the Power BI employee export.

## Engineered fields

The Gold table adds attrition and retention flags, business-friendly age/tenure/income/distance bands, rating labels, promotion wait bands, seven transparent factor flags, `descriptive_factor_count`, and `descriptive_factor_band`.

The factor band is not a machine-learning prediction. It simply counts the following conditions: overtime, frequent travel, job satisfaction 1–2, work-life balance 1–2, environment satisfaction 1–2, no stock options, and distance above 10.

