# A4 · Classification

[Assignment](docs/assignment.pdf) · [PDF report](61_report_1.pdf) · [Report source](docs/report_1.md)

The raw CSVs in `data/` contain 1,838 labelled customers and 789 test customers. Predict `Segmentation` (A–D); exclude `ID`. The meanings of the segments and `Var_1` are not supplied.

## Run

From `A4/`, install `requirements.txt`, then:

1. Run `python tune_svm.py` for the SVM search and predictions.
2. Run all cells in [61_random_forest.ipynb](notebooks/61_random_forest.ipynb) for the forest and Task 3.

The notebook shows the tables and plots. The report contains the explanations. The three test prediction files are `ova.csv`, `ovo.csv` and `rf.csv`, each with one `predicted` column in test-row order.

## Code

| File | Purpose |
|---|---|
| `preprocess.py` | Fill missing values, encode categories and scale features inside each fold. |
| `svm_classifier.py` + the two `61_classifier_*.py` entry points | Train and predict with OVA/OVO SVMs. |
| `tune_svm.py` | Search SVM settings on five folds. |
| `randomforest.py` | Bootstrap trees, combine votes, measure OOB accuracy and compare tree counts. |
| `task3_analysis.py` | Validation curves, model comparisons, baselines and statistical tests. |

`results/` keeps only the selected SVM settings, full CV search, one shared table of validation predictions, and three figures needed for the report. [inspect.ipynb](notebooks/inspect.ipynb) contains the original data exploration.

## Predict another test file

```bash
python 61_classifier_ova.py data/Customer_Test.csv
python 61_classifier_ovo.py data/Customer_Test.csv
```

Add `--selection macro_f1` to either command to generate the optional macro-F1-selected predictions. Accuracy and macro-F1 are both retained in the search results; optional prediction files are created only when requested.

## Section 1 submission

| Required file | Location |
|---|---|
| `61_classifier_ovo.py` | [OVO entry script](61_classifier_ovo.py) |
| `61_classifier_ova.py` | [OVA entry script](61_classifier_ova.py) |
| `61_random_forest.ipynb` | [Notebook](notebooks/61_random_forest.ipynb) |
| `61_report_1.pdf` | [Report](61_report_1.pdf) |

Include the supporting Python files, `requirements.txt`, `data/`, `results/`, and the three prediction CSVs. Preserve the folder layout so imports and file paths work.
