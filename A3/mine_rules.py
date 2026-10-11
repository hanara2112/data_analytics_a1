"""Part B: mine single-movie antecedent rules and compare thresholds."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth


# Start with higher support, then include less common movie combinations.
SUPPORT_VALUES = [0.10, 0.09, 0.08]
CONFIDENCE_VALUES = [0.10, 0.20, 0.30, 0.40, 0.50]

# Starting choice: review the experiment plots before justifying these values.
SELECTED_SUPPORT = 0.10
SELECTED_CONFIDENCE = 0.50


def single_movie_rules(itemsets, min_confidence):
    """Generate every qualifying {movie} -> remaining movies rule."""
    supports = dict(zip(itemsets["itemsets"], itemsets["support"]))
    rows = []

    for movies, support in supports.items():
        if len(movies) < 2:
            continue

        for movie in sorted(movies):
            antecedent = frozenset([movie])
            consequent = movies - antecedent
            confidence = support / supports[antecedent]

            if confidence >= min_confidence:
                rows.append({
                    "antecedent": [int(movie)],
                    "consequent": sorted(int(item) for item in consequent),
                    "support": support,
                    "confidence": confidence,
                    "lift": confidence / supports[consequent],
                })

    return pd.DataFrame(rows, columns=[
        "antecedent", "consequent", "support", "confidence", "lift"
    ])


def plot_experiments(experiments, output_dir):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    for support, results in experiments.groupby("min_support"):
        label = f"Support = {support:.2f}"
        axes[0].plot(results["min_confidence"], results["rule_count"],
                     marker="o", label=label)
        axes[1].plot(results["min_confidence"], results["median_lift"],
                     marker="o", label=label)

    axes[0].set(title="How many rules survive?", xlabel="Minimum confidence",
                ylabel="Number of rules")
    axes[0].set_yscale("symlog", linthresh=1)
    axes[1].set(title="How strong are the associations?",
                xlabel="Minimum confidence", ylabel="Median lift")
    axes[1].axhline(1, color="gray", linestyle="--")

    for axis in axes:
        axis.legend()
        axis.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(output_dir / "threshold_comparison.png", dpi=160)
    plt.close(fig)


def main():
    if SELECTED_SUPPORT not in SUPPORT_VALUES or SELECTED_CONFIDENCE not in CONFIDENCE_VALUES:
        raise ValueError("Selected thresholds must appear in the experiment grid.")

    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "mining_results"
    output_dir.mkdir(exist_ok=True)

    train = pd.read_json(base_dir / "processed" / "train.json")
    interactions = train.explode("movieIds")
    matrix = pd.crosstab(interactions["userId"], interactions["movieIds"]).gt(0)
    print(f"Training matrix: {matrix.shape}", flush=True)

    experiments = []
    selected_rules = None

    for support in SUPPORT_VALUES:
        print(f"Mining itemsets at support={support:.2f}...", flush=True)
        # No maximum length: consequents may contain one or more movies.
        itemsets = fpgrowth(matrix, min_support=support, use_colnames=True)
        candidates = single_movie_rules(itemsets, min(CONFIDENCE_VALUES))

        for confidence in CONFIDENCE_VALUES:
            rules = candidates.loc[candidates["confidence"] >= confidence].copy()
            experiments.append({
                "min_support": support,
                "min_confidence": confidence,
                "itemset_count": len(itemsets),
                "rule_count": len(rules),
                "median_confidence": rules["confidence"].median(),
                "median_lift": rules["lift"].median(),
                "mean_consequent_size": rules["consequent"].map(len).mean(),
            })
            print(f"  confidence={confidence:.2f}: {len(rules):,} rules", flush=True)

            if support == SELECTED_SUPPORT and confidence == SELECTED_CONFIDENCE:
                selected_rules = rules

        # Save progress after each completed support level.
        pd.DataFrame(experiments).to_csv(output_dir / "threshold_results.csv", index=False)

    if selected_rules is None:
        raise ValueError("Selected thresholds must appear in the experiment grid.")

    selected_rules = selected_rules.sort_values(
        ["confidence", "lift", "support"], ascending=False
    )
    titles = pd.read_csv(base_dir / "dataset" / "movies.csv").set_index("movieId")["title"]
    selected_rules["antecedent_title"] = selected_rules["antecedent"].map(
        lambda items: titles.loc[items[0]]
    )
    selected_rules["consequent_titles"] = selected_rules["consequent"].map(
        lambda items: [titles.loc[item] for item in items]
    )
    selected_rules.to_json(output_dir / "rules.json", orient="records", indent=2,
                           double_precision=15)
    settings = {
        "min_support": SELECTED_SUPPORT,
        "min_confidence": SELECTED_CONFIDENCE,
        "training_users": len(train),
        "rule_count": len(selected_rules),
    }
    (output_dir / "selected_thresholds.json").write_text(
        json.dumps(settings, indent=2), encoding="utf-8"
    )

    plot_experiments(pd.DataFrame(experiments), output_dir)
    print(f"\nSaved {len(selected_rules):,} selected rules and plots to {output_dir}")


if __name__ == "__main__":
    main()
