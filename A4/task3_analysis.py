"""Task 3 analysis. Run from A4 with: python task3_analysis.py"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold

from randomforest import RandomForest
from svm_classifier import predict_ova, train_ova
from tune_svm import prepare_folds


BASE = Path(__file__).resolve().parent
OUT = BASE / "results"
FIGURES = OUT / "figures"
LABELS = ["A", "B", "C", "D"]


def imbalance_experiment():
    results = pd.read_csv(OUT / "cv_results.csv")
    same_settings = results[
        (results.method == "ova") & (results.kernel == "rbf") &
        (results.C == 1) & (results.gamma == "0.1")
    ]
    return same_settings[["class_weight", "accuracy_mean", "macro_f1_mean"]]


def plot_curve(ax, rows, name, xlabel, log_x=False):
    values = pd.DataFrame(rows, columns=["value", "train_accuracy", "cv_accuracy"])
    values.insert(0, "curve", name)
    values.plot(x="value", y=["train_accuracy", "cv_accuracy"], marker="o", ax=ax)
    if log_x:
        ax.set_xscale("log")
    ax.set(xlabel=xlabel, ylabel="Accuracy", title=name)
    ax.legend(["Training", "Cross-validation"])
    return values


def validation_curves(folds):
    gamma_rows = []
    for gamma in [0.001, 0.01, 0.1, 1, 10]:
        train_scores, valid_scores = [], []
        for X_train, X_valid, y_train, y_valid, _ in folds:
            model = train_ova(X_train, y_train, {"kernel": "rbf", "C": 1, "gamma": gamma})
            train_scores.append(accuracy_score(y_train, predict_ova(model, X_train)))
            valid_scores.append(accuracy_score(y_valid, predict_ova(model, X_valid)))
        gamma_rows.append((gamma, np.mean(train_scores), np.mean(valid_scores)))

    depth_rows = []
    for depth in [2, 4, 6, 8, 12, 16, None]:
        train_scores, valid_scores = [], []
        for X_train, X_valid, y_train, y_valid, _ in folds:
            model = RandomForest(n_trees=100, max_depth=depth).fit(X_train, y_train)
            train_scores.append(accuracy_score(y_train, model.predict(X_train)))
            valid_scores.append(accuracy_score(y_valid, model.predict(X_valid)))
        depth_rows.append((depth if depth is not None else "unrestricted",
                           np.mean(train_scores), np.mean(valid_scores)))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    gamma = plot_curve(axes[0], gamma_rows, "OVA RBF gamma (C=1)", "Gamma", log_x=True)
    depth = plot_curve(axes[1], depth_rows, "Forest depth (100 trees)", "Max depth")
    fig.savefig(FIGURES / "task3_validation_curves.png", dpi=160)
    plt.close(fig)
    return pd.concat([gamma, depth], ignore_index=True)


def model_reports(actual, predictions):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    rows, summaries = [], []
    for ax, (name, predicted) in zip(axes, predictions.items()):
        matrix = confusion_matrix(actual, predicted, labels=LABELS)
        ax.imshow(matrix, cmap="Blues")
        ax.set(title=name.upper(), xlabel="Predicted", ylabel="Actual",
               xticks=range(4), yticks=range(4), xticklabels=LABELS, yticklabels=LABELS)
        for i in range(4):
            for j in range(4):
                ax.text(j, i, matrix[i, j], ha="center", va="center",
                        color="white" if matrix[i, j] > matrix.max() / 2 else "black")
        report = classification_report(actual, predicted, labels=LABELS,
                                       output_dict=True, zero_division=0)
        for label in LABELS + ["macro avg", "weighted avg"]:
            rows.append({"model": name, "class": label, **report[label]})
        pairs = [(matrix[i, j] + matrix[j, i], LABELS[i], LABELS[j])
                 for i in range(4) for j in range(i + 1, 4)]
        count, left, right = max(pairs)
        summaries.append({"Model": name.upper(), "Accuracy": report["accuracy"],
                          "Macro-F1": report["macro avg"]["f1-score"],
                          "Weighted-F1": report["weighted avg"]["f1-score"],
                          "Most confused": f"{left}/{right} ({count} errors)"})
    fig.savefig(FIGURES / "task3_confusion_matrices.png", dpi=160)
    plt.close(fig)
    return pd.DataFrame(summaries), pd.DataFrame(rows)


def compare_svms(actual, ova, ovo):
    ova_right = np.asarray(ova == actual)
    ovo_right = np.asarray(ovo == actual)
    difference = ovo_right.astype(int) - ova_right.astype(int)
    rng = np.random.default_rng(42)
    boot = [difference[rng.integers(len(difference), size=len(difference))].mean()
            for _ in range(10000)]
    low, high = np.quantile(boot, [0.025, 0.975])
    ovo_only = int((ovo_right & ~ova_right).sum())
    ova_only = int((ova_right & ~ovo_right).sum())
    p_value = binomtest(ovo_only, ovo_only + ova_only, 0.5).pvalue
    return pd.Series({"OVO minus OVA accuracy": difference.mean(),
                      "95% CI lower": low, "95% CI upper": high,
                      "Only OVO correct": ovo_only, "Only OVA correct": ova_only,
                      "McNemar p-value": p_value})


def baselines(X, actual, predictions):
    majority_predictions = np.empty(len(actual), dtype=object)
    random_predictions = np.empty(len(actual), dtype=object)
    rng = np.random.default_rng(42)
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for train_rows, valid_rows in splitter.split(X, actual):
        proportions = actual.iloc[train_rows].value_counts(normalize=True).reindex(LABELS)
        majority_predictions[valid_rows] = proportions.idxmax()
        proportions = proportions.to_numpy()
        random_predictions[valid_rows] = rng.choice(LABELS, size=len(valid_rows), p=proportions)

    rows = []
    for name, predicted in [("majority", majority_predictions), ("stratified random", random_predictions)]:
        rows.append({"Baseline": name, "Accuracy": accuracy_score(actual, predicted),
                     "Macro-F1": f1_score(actual, predicted, average="macro", zero_division=0)})
    best = max(predictions, key=lambda name: accuracy_score(actual, predictions[name]))
    correct = int((predictions[best] == actual).sum())
    baseline_rate = accuracy_score(actual, majority_predictions)
    p_value = binomtest(correct, len(actual), baseline_rate, alternative="greater").pvalue
    return pd.DataFrame(rows), best, p_value


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(BASE / "data/Customer_Train.csv")
    X = train.drop(columns=["ID", "Segmentation"])
    actual = train["Segmentation"]
    oof = pd.read_csv(OUT / "oof_predictions.csv")
    assert oof.ID.equals(train.ID) and oof.actual.equals(actual)
    predictions = {"ova": oof.ova, "ovo": oof.ovo, "rf": oof.rf}

    print("\nOVA class weights (C=1, RBF gamma=0.1):")
    print(imbalance_experiment().round(3).to_string(index=False))
    folds, fold_ids = prepare_folds(X, actual)
    assert np.array_equal(oof.fold, fold_ids)
    print("\nValidation curves:")
    print(validation_curves(folds).round(3).to_string(index=False))
    summary, metrics = model_reports(actual, predictions)
    print(summary.round(3).to_string(index=False))
    print(metrics.round(3).to_string(index=False))
    print(compare_svms(actual, oof.ova, oof.ovo).to_string())
    scores, best, p_value = baselines(X, actual, predictions)
    print(scores.round(3).to_string(index=False))
    print(f"Best by OOF accuracy: {best}; one-sided binomial p vs majority rate={p_value:.4g}")
    print("\nSaved Task 3 plots to", FIGURES)


if __name__ == "__main__":
    main()
