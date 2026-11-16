"""Shared preprocessing, fitted separately on each training fold."""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


def build_preprocessor():
    """Build a transformer; fit on training rows, then transform validation/test."""
    numeric_columns = ["Age", "Work_Experience", "Family_Size"]
    nominal_columns = ["Gender", "Ever_Married", "Graduated", "Profession", "Var_1"]

    numeric = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
    )
    nominal = make_pipeline(
        SimpleImputer(strategy="constant", fill_value="Missing"),
        OneHotEncoder(handle_unknown="ignore", sparse_output=False),
    )
    # Encoding Low/Average/High as 0/1/2 assumes equally spaced steps.
    spending = make_pipeline(
        SimpleImputer(strategy="most_frequent"),
        OrdinalEncoder(
            categories=[["Low", "Average", "High"]],
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        ),
        StandardScaler(),
    )

    return ColumnTransformer([
        ("numeric", numeric, numeric_columns),
        ("nominal", nominal, nominal_columns),
        ("spending", spending, ["Spending_Score"]),
    ])
