"""Five-fold search: raw data → fold preprocessing → SVMs → scores → selection."""

import json

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import ParameterGrid, StratifiedKFold

from preprocess import build_preprocessor
from svm_classifier import BASE_DIR, CLASSIFIERS, predict_file


# Gamma has no effect on a linear kernel, so do not search it there.
PARAM_GRID = [
    {"kernel": ["linear"], "C": [0.1, 1, 10], "class_weight": [None, "balanced"]},
    {
        "kernel": ["rbf"],
        "C": [0.1, 1, 10],
        "gamma": ["scale", 0.01, 0.1, 1.0],
        "class_weight": [None, "balanced"],
    },
]


def prepare_folds(X, y):
    """Fit a fresh preprocessor on each fold's training rows only.

    Preprocessing does not depend on SVM parameters, so these five transformed
    folds can be reused across configurations and both multiclass methods.
    """
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    folds = []
    fold_ids = np.zeros(len(y), dtype=int)
    for number, (train_rows, valid_rows) in enumerate(splitter.split(X, y), start=1):
        preprocessor = build_preprocessor()
        X_train = preprocessor.fit_transform(X.iloc[train_rows])
        X_valid = preprocessor.transform(X.iloc[valid_rows])
        folds.append((X_train, X_valid, y.iloc[train_rows], y.iloc[valid_rows], valid_rows))
        fold_ids[valid_rows] = number
    return folds, fold_ids


def search(method, folds, n_rows):
    """Keep both accuracy and macro-F1 winners from the same grid search."""
    fit, predict = CLASSIFIERS[method]
    configurations = ParameterGrid(PARAM_GRID)
    results = []
    best_selection_score = (-1.0, -1.0)
    best_params = None
    best_predictions = None
    best_macro_score = (-1.0, -1.0)
    best_macro_params = None

    for number, params in enumerate(configurations, start=1):
        accuracies, macro_f1s = [], []
        predictions = np.empty(n_rows, dtype=object)
        for X_train, X_valid, y_train, y_valid, valid_rows in folds:
            models = fit(X_train, y_train, params)
            predicted = predict(models, X_valid)
            # Restore original row positions so both methods remain comparable.
            predictions[valid_rows] = predicted
            accuracies.append(accuracy_score(y_valid, predicted))
            macro_f1s.append(f1_score(y_valid, predicted, average="macro", zero_division=0))

        result = {
            "method": method,
            "kernel": params["kernel"],
            "C": params["C"],
            "gamma": params.get("gamma", "not_applicable"),
            "class_weight": params["class_weight"] or "unweighted",
            "accuracy_mean": np.mean(accuracies),
            "accuracy_std": np.std(accuracies),
            "macro_f1_mean": np.mean(macro_f1s),
            "macro_f1_std": np.std(macro_f1s),
        }
        results.append(result)
        # Compare accuracy, then macro-F1; exact ties keep the earlier configuration.
        selection_score = (result["accuracy_mean"], result["macro_f1_mean"])
        if selection_score > best_selection_score:
            best_selection_score = selection_score
            best_params = params
            best_predictions = predictions
        macro_score = (result["macro_f1_mean"], result["accuracy_mean"])
        if macro_score > best_macro_score:
            best_macro_score = macro_score
            best_macro_params = params
        print(f"{method.upper()} {number:2}/{len(configurations)}: {params} "
              f"accuracy={result['accuracy_mean']:.4f} +/- {result['accuracy_std']:.4f}",
              flush=True)

    return results, best_params, best_predictions, best_macro_params


def main():
    # Start from all raw labelled data, not the prepared 80/20 CSVs.
    train = pd.read_csv(BASE_DIR / "data/Customer_Train.csv")
    X = train.drop(columns=["ID", "Segmentation"])
    y = train["Segmentation"]

    # Use exactly the same five folds for both methods.
    folds, fold_ids = prepare_folds(X, y)
    oof = pd.DataFrame({"ID": train["ID"], "actual": y, "fold": fold_ids})

    results = []
    selected = {}
    selected_macro = {}
    for method in CLASSIFIERS:
        method_results, best_params, predictions, best_macro_params = search(method, folds, len(y))
        results.extend(method_results)
        selected[method] = best_params
        selected_macro[method] = best_macro_params
        oof[method] = predictions
        print(f"Selected {method.upper()} by accuracy: {best_params}", flush=True)
        print(f"Selected {method.upper()} by macro-F1: {best_macro_params}", flush=True)

    output_dir = BASE_DIR / "results"
    output_dir.mkdir(exist_ok=True)
    pd.DataFrame(results).to_csv(output_dir / "cv_results.csv", index=False)
    (output_dir / "best_params.json").write_text(json.dumps(selected, indent=2) + "\n")
    (output_dir / "best_macro_params.json").write_text(json.dumps(selected_macro, indent=2) + "\n")
    oof.to_csv(output_dir / "oof_predictions.csv", index=False)

    # Refit on all labelled rows and predict the supplied test set.
    for method in CLASSIFIERS:
        predict_file(method, BASE_DIR / "data/Customer_Test.csv", output_dir / f"{method}.csv")

    print("\nSaved results to", output_dir)
    print("CV scores were used for selection; they are not independent test scores.")


if __name__ == "__main__":
    main()
