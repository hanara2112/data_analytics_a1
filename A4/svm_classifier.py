import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.svm import SVC

from preprocess import build_preprocessor


BASE_DIR = Path(__file__).resolve().parent


def _training_data(X, y):
    # Check inputs and record class order for pairs and exact ties.

    X, y = np.asarray(X), np.asarray(y)
    if X.ndim != 2 or y.ndim != 1 or len(X) != len(y):
        raise ValueError("Expected a feature matrix and one label per row.")

    first_training_row = {}
    for row, label in enumerate(y):
        if label not in first_training_row:
            first_training_row[label] = row

    if len(first_training_row) < 2:
        raise ValueError("Training requires at least two classes.")
    return X, y, first_training_row


def train_ova(X, y, params=None):
    """Fit one binary SVM per class: that class is 1, all others are 0."""
    X, y, first_training_row = _training_data(X, y)
    estimators = {}
    for label in first_training_row:
        binary_y = (y == label).astype(int)
        model = SVC(**(params or {}))
        model.fit(X, binary_y)
        estimators[label] = model
    return {"estimators": estimators, "first_training_row": first_training_row}


def predict_ova(models, X):
    """Return the class with the highest binary decision score per row."""
    X = np.asarray(X)
    classes = list(models["first_training_row"])
    scores = np.column_stack([
        models["estimators"][label].decision_function(X) for label in classes
    ])
    # Classes follow training-row order, which also resolves exact score ties.
    return np.asarray(classes)[np.argmax(scores, axis=1)]


def train_ovo(X, y, params=None):
    """Fit one binary SVM per pair, using only that pair's rows."""
    X, y, first_training_row = _training_data(X, y)
    estimators = {}
    for left, right in combinations(first_training_row, 2):
        mask = (y == left) | (y == right)
        binary_y = (y[mask] == right).astype(int)
        model = SVC(**(params or {}))
        model.fit(X[mask], binary_y)
        estimators[left, right] = model
    return {"estimators": estimators, "first_training_row": first_training_row}


def predict_ovo(models, X):
    """Choose by votes, then summed scores, then first training row."""
    X = np.asarray(X)
    first_training_row = models["first_training_row"]
    classes = list(first_training_row)
    class_column = {label: i for i, label in enumerate(classes)}
    votes = np.zeros((len(X), len(classes)), dtype=int)
    tie_scores = np.zeros_like(votes, dtype=float)

    # Fix summation order: floating-point addition can depend on operand order.
    pairs = sorted(
        models["estimators"],
        key=lambda pair: tuple(sorted(first_training_row[c] for c in pair)),
    )
    for left, right in pairs:
        model = models["estimators"][left, right]
        margin = model.decision_function(X)
        pair_predictions = model.predict(X)
        left_column = class_column[left]
        right_column = class_column[right]
        votes[:, left_column] += pair_predictions == 0
        votes[:, right_column] += pair_predictions == 1
        # Positive margins support the class encoded as 1 (right).
        tie_scores[:, left_column] -= margin
        tie_scores[:, right_column] += margin

    winners = []
    for row in range(len(X)):
        candidates = np.flatnonzero(votes[row] == votes[row].max())
        best_score = tie_scores[row, candidates].max()
        candidates = candidates[tie_scores[row, candidates] == best_score]
        winner = min(candidates, key=lambda i: first_training_row[classes[i]])
        winners.append(classes[winner])
    return np.asarray(winners, dtype=np.asarray(classes).dtype)


CLASSIFIERS = {
    "ova": (train_ova, predict_ova),
    "ovo": (train_ovo, predict_ovo),
}


def predict_file(method, test_file, output_file, selection="accuracy"):
    """Refit the selected model on all labelled rows and predict a raw CSV."""
    params_file = "best_params.json" if selection == "accuracy" else "best_macro_params.json"
    params = json.loads((BASE_DIR / "results" / params_file).read_text())[method]
    train = pd.read_csv(BASE_DIR / "data/Customer_Train.csv")
    test = pd.read_csv(test_file)
    X = train.drop(columns=["ID", "Segmentation"])
    y = train["Segmentation"]

    # Learn preprocessing from all labelled rows, test rows never affect the fit.
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(X)
    X_test = preprocessor.transform(test[X.columns])
    fit, predict = CLASSIFIERS[method]
    models = fit(X_train, y, params)
    predictions = predict(models, X_test)
    pd.DataFrame({"predicted": predictions}).to_csv(output_file, index=False)
    print(f"{method.upper()}: wrote {len(predictions)} predictions to {output_file}")
    return predictions


def run_classifier(method):
    """Command-line entry point shared by the two required scripts."""
    parser = argparse.ArgumentParser(description=f"Predict customer segments with {method.upper()}.")
    parser.add_argument("test_file", type=Path, help="Raw customer CSV, without labels")
    parser.add_argument("--selection", choices=["accuracy", "macro_f1"], default="accuracy")
    args = parser.parse_args()
    params_file = "best_params.json" if args.selection == "accuracy" else "best_macro_params.json"
    if not (BASE_DIR / "results" / params_file).exists():
        parser.error("Run tune_svm.py first to select and save hyperparameters.")
    suffix = "" if args.selection == "accuracy" else "_macro"
    predict_file(method, args.test_file, Path(f"{method}{suffix}.csv"), selection=args.selection)
