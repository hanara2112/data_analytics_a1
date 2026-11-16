# Assignment 4 — Team 61

[Assignment](docs/assignment.pdf) · [Section 1 report](docs/61_report_1.pdf) · [Report source](docs/report_1.md)

## Progress

Section 1 Tasks 1–3 have the required code, results and explanations. Section 2 Task 1 has the data, Power BI report and notes; these still need to be included in `61_report_2.pdf`. The clustering notebooks and Section 3 deliverables are not present yet.

| Requirement | Evidence |
|---|---|
| Section 1, Task 1: OVO/OVA | [Entry scripts and implementation](scripts/), [60 search configurations](results/cv_results.csv), [selected settings](results/best_params.json), [OVA predictions](results/ova.csv), [OVO predictions](results/ovo.csv). |
| Section 1, Task 2: random forest | [Implementation](scripts/randomforest.py), [executed notebook](notebooks/61_random_forest.ipynb), [789 predictions](results/rf.csv). Required tree counts, two depths, OOB/CV results and held-out permutation importance are present. |
| Task 3(a): class imbalance | Fixed-setting comparison of equal and balanced OVA weights, with explanation in the notebook and report. |
| Task 3(b): over/underfitting | Training/CV curves for gamma and tree depth; all requested hyperparameters discussed in the report. |
| Task 3(c): errors and metrics | Confusion matrices, per-class precision/recall/F1, macro/weighted F1 and most-confused segments for all three models. |
| Task 3(d): OVO versus OVA | Paired bootstrap interval and exact McNemar test; the report explains the preference for OVA. |
| Task 3(e): baselines and advice | Majority and stratified-random baselines, one-sided binomial test, practical interpretation and advice within 150 words. |
| Section 2, Task 1: Power BI | [PBIX](powerbi/61_clustering_Part1.pbix), [cleaned CSV](powerbi/61_marketing_cleaned.csv), [M query](powerbi/query.m), [existing DAX measures](powerbi/measures.dax), [cleaning notes](docs/task1_preprocessing_notes.md), [five checked insights](docs/section2_business_insights.md). |

Checked on 16 November 2026. All three fitted classifiers reproduced their 789 saved predictions. OOF rows and folds match the training data. Task 3 statistics were recalculated against the report, and all 12 validation-curve points reproduced the notebook values to three decimals. The full SVM grid and forest tree-count experiment were not rerun; their saved results were inspected.

Validation accuracy is 34.06% for OVA, 35.09% for OVO and 34.71% for the forest. Settings were selected on these folds, so these are not independent test scores. The report documents this and the OOB preprocessing limitation.

The PBIX contains categorical bars, age/income bins, a customer-level scatter plot, a correlation heatmap and slicers. Its embedded M query matches the saved file, and the spending, response-rate and customer-count DAX formulas were inspected. Live interaction was not tested. The heatmap is a fixed full-dataset correlation table; label it accordingly and remove its unused hidden income slicer. The cleaned data still contains three missing ages and eight flagged extreme incomes.

## Files

| Folder | Contents |
|---|---|
| [scripts/](scripts/) | All Python code, including the two required classifier entry points. |
| [results/](results/) | Section 1 predictions, search results, settings, OOF predictions and figures. |
| [notebooks/](notebooks/) | Forest experiments, Task 3 comparisons and initial data inspection. |
| [powerbi/](powerbi/) | Section 2 Task 1 report, cleaned CSV, M query and DAX measures. |
| [docs/](docs/) | Assignment, reports and notes. |
| [data/](data/) | Original datasets and supplied archive. |

## Run

From `A4/`, install `requirements.txt` in your Python environment.

```bash
python scripts/tune_svm.py
python scripts/61_classifier_ova.py data/Customer_Test.csv
python scripts/61_classifier_ovo.py data/Customer_Test.csv
python scripts/task3_analysis.py
```

Run `notebooks/61_random_forest.ipynb` after SVM tuning and before the standalone Task 3 script; it adds the forest's OOF predictions. The notebook also runs Task 3. The classifier commands write to `results/ova.csv` and `results/ovo.csv`; the notebook writes `results/rf.csv`. Add `--selection macro_f1` to either SVM command for the separately selected macro-F1 model.

For submission, include the scripts, executed notebook, Section 1 PDF, results, requirements and referenced data. Preserve this folder layout: the classifier entry points depend on the supporting scripts, training data and saved parameter files.
