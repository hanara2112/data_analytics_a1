# Assignment 1 — NYC Airbnb

This folder contains the complete Part II workflow, from the original Airbnb
data to the final report.

## Start here

If you only want the assignment result, read:

- `notes/PART_II_FINAL_REPORT.md` — short final report
- `notebooks/part_ii_analysis.ipynb` — complete analysis and evidence

For the full reasoning behind the cleaning and analysis, use
`notes/LISTINGS_WORKFLOW.md`.

## Folder guide

```text
listings.csv     original data
scripts/         inspection and cleaning code
notebooks/       visual inspection and final analysis
notes/           assignment PDF and written reports
figures/         report figures
artifacts/       generated CSV and audit logs
```

## Run the work

From this directory:

```bash
python3 scripts/extract.py
python3 scripts/cleanup.py
```

Then run the notebooks in this order:

1. `notebooks/listings_data_inspection.ipynb`
2. `notebooks/part_ii_analysis.ipynb`

The scripts keep all source rows. Missing values and unusual prices are flagged
rather than silently removed or filled in.
