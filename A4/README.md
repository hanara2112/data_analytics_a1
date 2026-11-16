# Assignment 4 — Team 61

[Assignment](docs/assignment.pdf) · [Section 1 report](docs/61_report_1.pdf)

Section 1 is done. Power BI work is in place; clustering, report 2 and the case study are left.

- `scripts/` — Python code
- `notebooks/61_random_forest.ipynb` — forest experiments and Task 3
- `results/` — predictions, CV results and plots
- `powerbi/` — PBIX, cleaned CSV, M and DAX
- `docs/` — reports and notes
- `data/` — original datasets

Run from `A4/` with `requirements.txt` installed:

```bash
python scripts/tune_svm.py
```

Then run the forest notebook. To generate SVM predictions using saved settings:

```bash
python scripts/61_classifier_ova.py data/Customer_Test.csv
python scripts/61_classifier_ovo.py data/Customer_Test.csv
```

Predictions go into `results/`. Keep the folder structure when submitting.
