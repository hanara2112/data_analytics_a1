"""Assignment 4 random forest: bootstrap trees, vote, and score OOB rows."""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

from preprocess import build_preprocessor

BASE = Path(__file__).resolve().parent.parent
COUNTS = [1, 5, 10, 25, 50, 100, 200]

class RandomForest:
    def __init__(self, n_trees=200, max_depth=None):
        self.n_trees, self.max_depth = n_trees, max_depth

    def fit(self, X, y):
        # Match sklearn's feature precision when growing and traversing nodes.
        X, y = np.asarray(X, dtype=np.float32), np.asarray(y)
        self.classes_ = np.unique(y)
        self.X_train_, self.y_train_ = X, y
        self.trees_, self.oob_rows_ = [], []
        rng = np.random.default_rng(42)
        for _ in range(self.n_trees):
            sample = rng.integers(len(y), size=len(y))  # bootstrap rows
            in_bag = np.zeros(len(y), dtype=bool)
            in_bag[sample] = True
            tree_rng = np.random.default_rng(rng.integers(2**31))
            tree = self._grow_tree(X[sample], y[sample], depth=0, rng=tree_rng)
            self.trees_.append(tree)
            self.oob_rows_.append(np.flatnonzero(~in_bag))
        return self

    def _grow_tree(self, X, y, depth, rng):
        labels, counts = np.unique(y, return_counts=True)
        leaf = labels[counts.argmax()]
        if len(labels) == 1 or len(y) < 10:
            return leaf
        if self.max_depth is not None and depth >= self.max_depth:
            return leaf

        # Choose new candidate features here, separately at every node.
        features = rng.choice(X.shape[1], max(1, int(np.sqrt(X.shape[1]))), replace=False)
        stump = DecisionTreeClassifier(max_depth=1, min_samples_leaf=5,
                                       max_features=None, random_state=int(rng.integers(2**31)))
        stump.fit(X[:, features], y)  # sklearn finds one split among our candidates.
        if stump.tree_.node_count == 1:
            return leaf
        feature = features[stump.tree_.feature[0]]
        threshold = stump.tree_.threshold[0]
        left = X[:, feature].astype(float) <= threshold
        return (feature, threshold,
                self._grow_tree(X[left], y[left], depth + 1, rng),
                self._grow_tree(X[~left], y[~left], depth + 1, rng))

    def _predict_tree(self, tree, X):
        labels = []
        for row in X:
            node = tree
            while isinstance(node, tuple):  # split: feature, threshold, left, right
                feature, threshold, left, right = node
                node = left if float(row[feature]) <= threshold else right
            labels.append(node)
        return np.asarray(labels, dtype=self.classes_.dtype)

    def _votes(self, X, n_trees, oob=False):
        votes = np.zeros((len(X), len(self.classes_)), dtype=int)
        all_rows = np.arange(len(X))
        for tree, excluded in zip(self.trees_[:n_trees], self.oob_rows_[:n_trees]):
            rows = excluded if oob else all_rows
            labels = self._predict_tree(tree, X[rows])
            np.add.at(votes, (rows, np.searchsorted(self.classes_, labels)), 1)
        return votes

    def predict(self, X, n_trees=None):
        n_trees = self.n_trees if n_trees is None else n_trees
        votes = self._votes(np.asarray(X, dtype=np.float32), n_trees)
        return self.classes_[votes.argmax(axis=1)]

    def oob_accuracy(self, n_trees=None):
        n_trees = self.n_trees if n_trees is None else n_trees
        votes = self._votes(self.X_train_, n_trees, oob=True)
        covered = votes.sum(axis=1) > 0
        if not covered.any():
            return float("nan"), 0.0
        correct = self.classes_[votes[covered].argmax(axis=1)] == self.y_train_[covered]
        return float(correct.mean()), float(covered.mean())

def run_experiment():
    raw = pd.read_csv(BASE / "data/Customer_Train.csv")
    X = raw.drop(columns=["ID", "Segmentation"])
    y = raw["Segmentation"]
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rows = []
    for depth in [8, None]:
        for train_rows, valid_rows in folds.split(X, y):
            prep = build_preprocessor()
            X_train = prep.fit_transform(X.iloc[train_rows])
            X_valid = prep.transform(X.iloc[valid_rows])
            forest = RandomForest(max_depth=depth).fit(X_train, y.iloc[train_rows])
            for n in COUNTS:
                oob, coverage = forest.oob_accuracy(n)
                cv = accuracy_score(y.iloc[valid_rows], forest.predict(X_valid, n))
                rows.append(("unrestricted" if depth is None else str(depth), n, oob, coverage, cv))
    scores = pd.DataFrame(rows, columns=["max_depth", "n_trees", "oob", "coverage", "cv"])
    summary = scores.groupby(["max_depth", "n_trees"], sort=False).agg(
        oob_accuracy_mean=("oob", "mean"), oob_accuracy_std=("oob", "std"),
        oob_coverage_mean=("coverage", "mean"),
        cv_accuracy_mean=("cv", "mean"), cv_accuracy_std=("cv", "std"),
    ).reset_index()
    return summary


def plot_results(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    chart = summary.rename(columns={"oob_accuracy_mean": "OOB", "cv_accuracy_mean": "CV"})
    chart = chart.pivot(index="n_trees", columns="max_depth", values=["OOB", "CV"])
    ax = chart.plot(marker="o", figsize=(9, 4))
    ax.set_xscale("log")
    ax.set_xticks(COUNTS, labels=COUNTS)
    ax.set(xlabel="Number of trees", ylabel="Accuracy")
    ax.legend(["OOB (depth 8)", "OOB (unrestricted)", "CV (depth 8)", "CV (unrestricted)"], title="")
    output = BASE / "results/figures"
    output.mkdir(parents=True, exist_ok=True)
    ax.figure.savefig(output / "rf_tree_count_accuracy.png", dpi=160)
    plt.close(ax.figure)


def main():
    summary = run_experiment()
    plot_results(summary)
    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
