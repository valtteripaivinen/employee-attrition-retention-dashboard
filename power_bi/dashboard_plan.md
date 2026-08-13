# Power BI dashboard plan

Import all four CSV exports. Rename `hr_employee_analytics` to `HR` and `hr_attrition_drivers` to `Drivers`. The department and job-role summary files are optional validation tables; the main visuals can be built from `HR`.

Do not create relationships between `HR` and `Drivers`. `Drivers` contains the same workforce summarized repeatedly across several dimensions and is intended only for its own aggregate ranking visual.

## Page 1 — Workforce Overview

- Slicers: Department, Job Role, Gender, Age Band.
- KPI cards: Headcount, Attritions, Attrition Rate %, Average Age, Average Years at Company.
- Donut chart: Headcount by Department.
- Bar chart: Headcount by Job Role.
- Clustered bar chart: Headcount and Attritions by Department.
- Matrix: Department rows, Job Role columns, Headcount as values.
- Footer note: “Fictional IBM-created practice dataset; results do not describe IBM’s real workforce.”

## Page 2 — Attrition Drivers

- KPI cards: Attrition Rate %, Overtime Attrition Rate %, Non-Overtime Attrition Rate %, Overtime Attrition Gap.
- Bar chart: Attrition Rate % by Job Role.
- Clustered column chart: Attrition Rate % by Over Time.
- Bar chart: Attrition Rate % by Business Travel.
- Heatmap-style matrix: Age Band rows, Tenure Band columns, Attrition Rate % as values with conditional formatting.
- Separate Drivers chart: category on axis and Driver Attrition Lift as value; add `dimension` as a slicer and filter `headcount >= 25`.

## Page 3 — Employee Experience

- KPI cards: Average Job Satisfaction, Average Environment Satisfaction, Average Work-Life Balance, Average Job Involvement.
- Column chart: Attrition Rate % by Job Satisfaction Label.
- Column chart: Attrition Rate % by Work-Life Balance Label.
- Bar chart: Attrition Rate % by Environment Satisfaction Label.
- Matrix: Job Satisfaction Label rows, Work-Life Balance Label columns, Headcount and Attrition Rate % as values.
- Bar chart: Headcount by Descriptive Factor Band, with Attrition Rate % in the tooltip.
- Note: “The factor band is a transparent descriptive indicator, not an individual prediction.”

## Page 4 — Compensation & Career

- KPI cards: Average Monthly Income, Average Salary Hike %, Average Years Since Promotion, Average Years at Company.
- Bar chart: Average Monthly Income by Job Role.
- Column chart: Average Monthly Income by Job Level.
- Scatter chart: Average Monthly Income on X, Attrition Rate % on Y, Job Role as details, Headcount as size.
- Bar chart: Attrition Rate % by Income Band.
- Column chart: Attrition Rate % by Promotion Wait Band.
- Matrix: Job Role rows, Job Level columns, Average Monthly Income as values.

## Visual design

- Canvas: 16:9.
- Background: warm white or very light grey.
- Primary colour: dark navy or deep teal.
- Attrition: muted coral/red; retained employees: green; neutral benchmark: grey.
- Keep KPI cards aligned in one row and use consistent spacing.
- Percentages: one decimal; headcount: whole number; income: whole number without a currency symbol because the source does not specify a currency.
- Keep each page to approximately five or six visuals.
- Add a small dataset and ethics note to every page.

