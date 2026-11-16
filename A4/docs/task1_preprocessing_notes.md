# Section 2, Task 1: Preprocessing notes

The original dataset had 2,240 customers and 29 columns, with no duplicate IDs. Comparing the exported CSV by customer ID confirmed that its values match the rules in `../powerbi/query.m`. All customers were retained, and seven added columns increased the total to 36.

The 24 missing incomes were filled with the median of 51,381.5. Eight incomes above the upper IQR fence of 118,350.5 were flagged but left unchanged. This retains those customers for other analyses while marking their incomes for review; income-based results should state whether they include these rows. Three birth years—1893, 1899 and 1900—implied ages above 100, so their cleaned birth years and ages were set to null. The original birth years were preserved. Three `Alone` values became `Single`, while two `Absurd` and two `YOLO` values became `Unknown`.

Age and tenure use 29 June 2014, the latest enrollment date, so they describe the historical dataset rather than change with today's date. Age is approximately 2014 minus birth year; tenure is the number of days since enrollment. Valid ages range from 18 to 74, and tenure ranges from 0 to 699 days.

Total spending sums the six product-spending columns. Total purchases sums web, catalog and store purchases, excluding deal purchases to avoid overlap. Total children adds `Kidhome` and `Teenhome`. These five features, the cleaned birth year and the income-outlier flag account for the seven added columns.

The final dataset has no missing incomes, but three ages remain unknown. Mean income is 52,237.98, including the flagged values. Total spending is 1,356,988 monetary units, with a mean of 605.80 and a median of 396 per customer. The latest campaign received 334 responses, giving a response rate of 14.91%.

The PBIX contains the required categorical charts, age and income bins, a customer-level scatter plot, a correlation heatmap and slicers. Its embedded M query matches `../powerbi/query.m`. Three DAX measures were verified: total spending, campaign response rate and customer count; their formulas are saved in `../powerbi/measures.dax`. Five checked findings are in `section2_business_insights.md`. This was a file inspection, not a live test of the report in Power BI.

The heatmap uses a calculated table, so its correlations stay fixed when slicers change. Label it as the full-dataset correlation matrix. Page 6 also contains a hidden income slicer selected to 160,000–169,999; remove that unused slicer to avoid confusion. The M query calculates an audit summary but returns only the customer table, so include the cleaning counts above in the report.

The CSV preserves the imputed .5 and the model stores Income as a decimal. For consistency, the M query's initial Income type could also be changed from `Int64.Type` to `type number`. Before clustering, decide how to handle the three missing ages and eight extreme incomes. The CSV and PBIX already have the required submission names. The plots, cleaning explanation and insights still need inclusion in `61_report_2.pdf`.
