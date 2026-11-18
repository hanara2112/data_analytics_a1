# Task 1 — Power BI

[PBIX](../powerbi/61_clustering_Part1.pbix) · [Cleaned CSV](../powerbi/61_marketing_cleaned.csv) · [Power Query](../powerbi/query.m) · [DAX](../powerbi/measures.dax)

Started with **2,240 customers and 29 columns**. The cleaned file has **2,240 customers and 36 columns**. No rows were removed; IDs are unique. The CSV was checked against the Power Query rules.

## What changed

| Issue | Count | Change |
| --- | ---: | --- |
| Missing income | 24 | Filled with the median, 51,381.5. |
| Income above 118,350.5 (upper IQR limit) | 8 | Flagged, but kept unchanged. |
| Birth years 1893, 1899 and 1900 | 3 | Cleaned birth year and age set to null; original year kept. |
| Marital status `Alone` | 3 | Changed to `Single`. |
| Marital status `Absurd` or `YOLO` | 4 | Changed to `Unknown`. |

Five features were calculated for all customers; age remains missing for three:

- Age: 2014 minus birth year, so it is approximate.
- Tenure: days from enrollment to 29 June 2014.
- Total spending: sum of the six product amounts.
- Total purchases: web + catalog + store. Deals are excluded to avoid counting purchases twice.
- Total children: `Kidhome + Teenhome`.

29 June 2014 is the latest enrollment date. Using this fixed date keeps age and tenure relevant to the data and gives the same result each time. The five features, cleaned birth year and income flag make up the seven new columns.

No incomes are missing now. Valid ages are 18–74; tenure is 0–699 days. Mean income is 52,237.98, including the eight flagged values. Total spending is 1,356,988; mean spending is 605.80 and median spending is 396. There were 334 campaign responses out of 2,240 customers (**14.91%**).

## What the data shows

1. Married and Together account for 1,444 customers (64.46%). Household-based offers are worth testing with this large group.
2. Ages 40–49 are the largest age group: 676 customers, or 30.22% of valid ages. Compare their spending with other ages before making them a campaign priority.
3. The 30,000–39,999 income band has 362 customers (16.16%). Compare its spending and response rates with nearby bands when planning offers.
4. Purchases and spending have a correlation of 0.821. Purchase frequency could help identify higher-spending customers, though it does not show profit.
5. Income and spending correlate at 0.665, rising to 0.820 without the eight flagged incomes. Those values affect the result enough to matter when targeting by income.

## Before submitting

The PBIX file contains the required charts, slicers and three DAX measures: spending, response rate and customer count. This was checked from the file; live slicer behaviour has not been tested.

- Label the heatmap as full-dataset correlations: it does not change with slicers.
- Remove the unused hidden income slicer on page 6, currently set to 160,000–169,999.
- Put the plots, cleaning counts and findings into `61_report_2.pdf`.

Task 2 handles the remaining missing ages and extreme incomes in the [K-Means notebook](../notebooks/61_clustering_Part2.ipynb).
