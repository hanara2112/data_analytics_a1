from pathlib import Path
import pandas as pd

data_dir = Path(__file__).resolve().parent / "dataset"
output_dir = data_dir.parent / "processed"
output_dir.mkdir(exist_ok=True)

# Keep positive interactions, with each user–movie pair appearing once.
ratings = pd.read_csv(data_dir / "ratings.csv")
liked = ratings.loc[ratings["rating"] >= 3.0, ["userId", "movieId"]]
liked = liked.drop_duplicates(["userId", "movieId"])

# Each transaction contains one user's unique liked movies.
transactions = (
    liked.groupby("userId")["movieId"]
    .agg(list)
    .rename("movieIds")
    .reset_index()
)

transactions = transactions.loc[
    transactions["movieIds"].str.len() >= 5
].reset_index(drop=True)

# Split whole user transactions, keeping users separate across sets.
train = transactions.sample(frac=0.8, random_state=42)
test = transactions.drop(train.index)

transactions.to_json(output_dir / "transactions.json", orient="records", indent=2)
train.to_json(output_dir / "train.json", orient="records", indent=2)
test.to_json(output_dir / "test.json", orient="records", indent=2)

print(f"Users: {len(transactions)}")
print(f"Training transactions: {len(train)}")
print(f"Test transactions: {len(test)}")