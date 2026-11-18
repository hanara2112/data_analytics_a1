# Assignment 4 — Team 61

[Assignment](docs/assignment.pdf) · [Section 1 report](docs/61_report_1.pdf) · [Report 1 source](docs/61_report_1.md) · [Report 2 draft](docs/61_report_2.md) · [Power BI notes](docs/section2_task1_notes.md)

Section 1 and Section 2 Tasks 1–3 are done. Report 2 is drafted in Markdown; its PDF export and the case study are left.

- `scripts/` — Python code
- `notebooks/61_random_forest.ipynb` — forest experiments and Task 3
- `notebooks/61_clustering_Part2.ipynb` — K-Means experiments and customer segments
- `notebooks/61_clustering_Part3.ipynb` — algorithm comparisons, parameter selection and scores
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

For K-Means, run `notebooks/61_clustering_Part2.ipynb` top to bottom. It saves scores and customer labels in `results/`.
