"""Save the figures used in docs/61_report_2.md."""

import base64
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "results/figures/report2"
OUT.mkdir(parents=True, exist_ok=True)

customers = pd.read_csv(BASE / "powerbi/61_marketing_cleaned.csv")
customers.columns = customers.columns.str.extract(r"\[([^\]]+)\]$", expand=False)


def save(fig, name):
    fig.savefig(OUT / name, dpi=180, bbox_inches="tight")
    plt.close(fig)


# Use the saved notebook plots rather than rerunning the experiments.
plots = {
    "61_clustering_Part2.ipynb": ["customer_k.png"],
    "61_clustering_Part3.ipynb": [
        "datasets.png", "dataset_k.png", "k_distance.png", "compact.png",
        "well_separated.png", "skewed.png", "subclusters.png", "dendrogram.png",
    ],
}
for notebook, names in plots.items():
    content = json.loads((BASE / "notebooks" / notebook).read_text())
    images = [output["data"]["image/png"] for cell in content["cells"]
              for output in cell.get("outputs", [])
              if "image/png" in output.get("data", {})]
    assert len(images) == len(names), notebook
    for name, image in zip(names, images):
        (OUT / name).write_bytes(base64.b64decode(image))

fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
for ax, column in zip(axes, ["Education", "Marital_Status"]):
    counts = customers[column].value_counts().sort_values()
    bars = ax.barh(counts.index, counts.values, color="steelblue")
    ax.bar_label(bars, padding=3)
    ax.set(title=column.replace("_", " "), xlabel="Customers")
    ax.set_xlim(0, counts.max() * 1.15)
save(fig, "categories.png")

fig, axes = plt.subplots(1, 3, figsize=(13, 3.5), layout="constrained")
axes[0].hist(customers.Age.dropna(), bins=np.arange(10, 81, 10), edgecolor="white")
axes[0].set(title="Age (2,237 known)", xlabel="Age in 2014", ylabel="Customers")
axes[1].hist(customers.Income, bins=np.arange(0, 680001, 10000), edgecolor="white")
axes[1].set(title="Income: all 2,240 customers", xlabel="Income", ylabel="Customers")
regular = customers[customers.Income_Outlier_Flag == 0]
axes[2].hist(regular.Income, bins=np.arange(0, 120001, 10000), edgecolor="white")
axes[2].set(title="Income: 2,232 unflagged customers", xlabel="Income", ylabel="Customers")
for ax in axes[1:]:
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x / 1000:g}"))
    ax.set_xlabel("Income (thousands)")
save(fig, "distributions.png")

fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
for ax, frame, title in zip(axes, [customers, regular],
                            ["All customers", "Excluding 8 flagged incomes"]):
    ax.scatter(frame.Income, frame.Total_Spending, s=9, alpha=.35)
    r = frame.Income.corr(frame.Total_Spending)
    ax.set(title=f"{title} (r={r:.3f})", xlabel="Income", ylabel="Total spending")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x / 1000:g}"))
    ax.set_xlabel("Income (thousands)")
save(fig, "income_spending.png")

columns = ["Age", "Income", "Total_Spending", "Total_Purchases",
           "Total_Children", "Customer_Tenure_Days", "Recency"]
names = ["Age", "Income", "Spending", "Purchases", "Children", "Tenure", "Recency"]
corr = customers[columns].corr()
fig, ax = plt.subplots(figsize=(7, 6), layout="constrained")
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set(xticks=range(7), xticklabels=names, yticks=range(7), yticklabels=names,
       title="Pearson correlations: full cleaned dataset")
plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
for i in range(7):
    for j in range(7):
        ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                color="white" if abs(corr.iloc[i, j]) > .6 else "black")
fig.colorbar(im, ax=ax, shrink=.8)
save(fig, "correlations.png")

labels = pd.read_csv(BASE / "results/customer_clusters.csv")
profile = customers.merge(labels, on="ID", validate="one_to_one")
assert len(profile) == len(customers) and profile.cluster.notna().all()
means = profile.groupby("cluster")[["Total_Spending", "Total_Children", "Total_Purchases"]].mean()
fig, axes = plt.subplots(1, 3, figsize=(11, 3.5), layout="constrained")
for ax, column in zip(axes, means.columns):
    bars = ax.bar(["Cluster 0", "Cluster 1"], means[column], color=["steelblue", "darkorange"])
    ax.bar_label(bars, fmt="%.2f", padding=3)
    ax.set(title=column.replace("_", " "), ylabel="Mean per customer",
           ylim=(0, means[column].max() * 1.2))
save(fig, "customer_profiles.png")
print(f"Saved {len(list(OUT.glob('*.png')))} figures to {OUT}")
