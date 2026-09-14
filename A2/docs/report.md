# Assignment 2 — Part 2

## Aim and data

Two methods are used to summarize the census survey data:

- **Attribute-Oriented Induction (AOI):** replace detailed values with broader groups, then describe the people whose income is above $50,000.
- **Bottom-Up Cube (BUC):** count records for different combinations of attributes and keep combinations that occur often enough.

The file contains **299,285 records and 42 columns** from the 1994 and 1995 surveys. The `income` column divides the records into two classes:

| Income class    | Records | Share of the dataset |
| --------------- | ------: | -------------------: |
| Above $50,000   |  18,568 |                6.20% |
| At most $50,000 | 280,717 |               93.80% |

Each row contributes one count. `instance_weight` is excluded from the BUC dimensions because it is a sampling weight. The percentages describe the supplied records rather than the whole US population.

### Data preparation

The same loading function is used throughout. It strips surrounding spaces and changes `?`, `NA`, and empty values to `Unknown`. `Not in universe` remains separate because it means that a question does not apply. The **6,735 repeated rows beyond their first occurrence** are retained because matching survey responses do not prove accidental duplication.

Missing migration information follows the survey year. In `migration_reg`, all **149,642 records from 1995** are unknown, while none of the **149,643 records from 1994** are unknown. Removing these records would remove an entire survey year, so they are retained.

## 1. Attribute-Oriented Induction

### Forming broader groups

AOI makes a detailed table easier to describe. For example, instead of treating every age as a separate value, it can use age ranges. A **concept hierarchy** is the set of rules that says which broader group each value belongs to.

The rules are stored in `hierarchies.json`. Five attributes are used for AOI:

| Attribute    | Grouping used                                                                                                         |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| Age          | Exact age → 0–17, 18–34, 35–49, 50–64, or 65–90                                                                 |
| Education    | Original qualification → children, below high school, high school, some college/associate, bachelor, or postgraduate |
| Industry     | 52 detailed codes → 24 major industries → 8 broad groups                                                            |
| Occupation   | 47 detailed codes → 15 major occupations → 7 broad groups                                                           |
| Worker class | 9 original categories → government, private, self-employed, never worked, without pay, or not in universe            |

For example, federal, state, and local government workers all become `Government`. Both original self-employment categories become `Self-employed`. These broader groupings were choices for this analysis.

The same grouping rules are applied to both income classes. Limiting each attribute to **8 values** reduces the table to **1,725 distinct combinations**. This still exceeds the chosen limit of **500 combinations**, so industry is replaced with `ALL`, meaning any industry. The result contains **439 combinations** described by age group, education group, occupation group and worker class.

Records with the same resulting description were merged, but their counts were added rather than discarded. The final table still accounts for all **299,285 records**, including all **18,568 high-income records**.

### Checking the supplied hierarchies

The assignment provides detailed and summary columns for industry, occupation, household relationship and previous residence. Applying the stored mappings checks whether the supplied summaries can be reproduced.

| Detailed → summary pair                    | What the check found                                                                                      |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Industry code → major industry             | Every detailed code had one summary value; all records matched.                                           |
| Occupation code → major occupation         | Every detailed code had one summary value; all records matched.                                           |
| Household relationship → household summary | `In group quarters` had 7 different summary values across 279 records. All other records matched.       |
| Previous state → previous region           | `Unknown` and `Abroad` each had 2 summary values, affecting 1,974 records. All other records matched. |

The conflicting household and previous-state values cannot be assigned one summary without an extra assumption. They are marked as `Ambiguous` instead of choosing the most common value. BUC uses the original summary columns, so this check does not overwrite them.

### Characteristic rules: which groups describe the high-income class?

A **t-weight** answers: **what percentage of all high-income records belong to this group?**

```text
t-weight = high-income records in the group / 18,568 × 100
```

The following are the three groups containing the most high-income records. All three are aged **35–49** and belong to the **professional and managerial occupation group**.

| Education    | Worker class | Income > $50K | Income ≤ $50K | t-weight | High-income share within the group |
| ------------ | ------------ | ------------: | -------------: | -------: | ---------------------------------: |
| Bachelor     | Private      |         1,552 |          2,453 |    8.36% |                             38.75% |
| Postgraduate | Private      |         1,400 |          1,019 |    7.54% |                             57.88% |
| Postgraduate | Government   |           673 |          1,367 |    3.62% |                             32.99% |

For the first group, `1,552 / 18,568 × 100 = 8.36%`. In words: **8.36% of the high-income records describe people aged 35–49 with a bachelor qualification, in the professional and managerial group, working for a private employer.**

The bachelor/private group covers more of the high-income class than the postgraduate/private group. However, the postgraduate/private group has a larger high-income share among its own members: **57.88% versus 38.75%**. These are different questions, which is why both percentages matter.

### Discriminant rules: which groups have a high share of high-income records?

A **d-weight** answers: **among everyone matching this description, what percentage have income above $50,000?**

```text
d-weight = high-income records in the group / all records in the group × 100
```

Groups are ranked by this percentage. A rule must contain at least **100 high-income records** and exceed the dataset's **6.20%** baseline. This prevents very small groups from dominating the result.

The top two groups were both **self-employed**, **postgraduate**, and in the **professional and managerial occupation group**:

| Age    | Income > $50K | Income ≤ $50K | t-weight | d-weight |
| ------ | ------------: | -------------: | -------: | -------: |
| 35–49 |           531 |            352 |    2.86% |   60.14% |
| 50–64 |           296 |            200 |    1.59% |   59.68% |

For the first group, `531 / (531 + 352) × 100 = 60.14%`. High income is much more common in this group than in the dataset overall. But the group contains only **2.86% of all high-income records**. A group can therefore distinguish high income well while describing only a small part of the high-income class.

These results describe associations in the records. They do not show that a qualification or type of work causes a particular income.

## 2. BUC implementation

### What the algorithm counts

A BUC **dimension** is an attribute used to group records. The cube uses these **12 original attributes**:

> Survey year, sex, race, education, marital status, employment status, worker class, major industry, major occupation, tax-filer status, household summary, and region of previous residence.

These attributes have between 2 and 24 values each. Summary industry and occupation fields avoid unnecessary splitting into small groups. Income remains separate from the 12 dimensions.

A **cube** contains counts at different levels of detail: for example, the count of female records, the count of female high-school graduates, and the count of all records. `ALL` means that an attribute is not restricted in that particular count.

The **minimum support**, called `minsup` in the code, is the smallest count retained. Keeping only counts that meet it produces an **iceberg cube**. The main run uses **30,000 records**.

### 2.1 In-memory version

The in-memory version keeps the working records in memory. It accepts the dimension list, the measure, and `minsup`. The implemented measure is **record count**, corresponding to `COUNT(*)`; other measures are rejected.

The algorithm works as follows:

1. Count the records in the current group. Keep the result if it meets `minsup`.
2. Split that group by the values of another dimension, such as worker class.
3. Repeat the process for each qualifying smaller group and the remaining dimensions.
4. Stop exploring a group as soon as its count falls below `minsup`.

Stopping is safe because adding conditions cannot increase the count. If fewer than 30,000 records match a worker class, fewer than 30,000 can match that worker class **and** a particular education level.

The code also considers combinations that skip dimensions, so it includes totals over any subset of the 12 attributes. It uses array sorting and slicing to form groups. It does not use a dataframe `groupby` or a database engine to compute the BUC result.

### 2.2 Out-of-memory version

The second version accepts a memory allowance. It reads the input in small blocks rather than loading all working records at once.

For a group that is too large to process within the allowance, it first counts the values of the next dimension. It then reads the group again and writes qualifying smaller groups to temporary files. Each file is processed in turn. A group that fits is passed to the same in-memory procedure; a group that remains too large stays on disk and is split further. Results are written as they are produced, and temporary files are removed after use.

The memory allowance includes space for the working records, temporary arrays used during sorting, and bookkeeping. **It is not a limit on the total memory used by Python, the notebook, or the operating system.** The reported peak is calculated from these allocations; it is not a measurement of total process memory.

### Results and correctness checks

Both versions processed all **299,285 records** with **12 dimensions** and `minsup = 30,000`.

| Result                            |    In-memory BUC | Disk-backed BUC |
| --------------------------------- | ---------------: | --------------: |
| Counts retained                   |            3,921 |           3,921 |
| Working-memory allowance          | No imposed limit |          16 MiB |
| Groups written to temporary files |                0 |             370 |

One MiB is 1,048,576 bytes. Writing **370 groups** confirms that the second version actually used disk storage in this run.

Examples from the main cube are:

| Conditions; all other attributes unrestricted | Records |
| --------------------------------------------- | ------: |
| No restrictions                               | 299,285 |
| Female                                        | 155,775 |
| Male and private worker class                 |  56,930 |
| Female and high-school graduate               |  40,154 |

The cube contains overlapping counts: female high-school graduates are also included in the female total. Adding all 3,921 counts would therefore count records more than once.

Every combination and count is compared between both implementations and DuckDB. All match. A single 12-dimensional DuckDB query exceeded its memory limit, so the reference uses **16 non-overlapping batches**. Each batch applies `CUBE` to the final eight dimensions and fixes one subset of the first four. Together, the batches cover all **4,096 dimension subsets** without sampling. DuckDB is used only for validation.

Small cases are also counted independently. They cover empty input, one record, repeated records, uneven group sizes, unknown values, support boundaries, changed dimension order and forced disk use. All checks pass.

## 3. Performance analysis

Each setting was run **three times** on the full dataset. The tables show median times; plot bars span the shortest and longest runs. All **39 measurements**, including the optimization experiment, are in `results/benchmark_runs.csv`.

Timing includes computation and temporary-file reads and writes. It excludes data preparation, DuckDB checks and plotting. Timed runs discard output after counting. The operating system's file cache was not cleared.

### 3.1 Minimum support versus runtime

Fixed: **12 dimensions and 16 MiB**.

| Minimum support | Median time | Counts retained |
| --------------: | ----------: | --------------: |
|          15,000 |     8.291 s |           9,593 |
|          30,000 |     5.498 s |           3,921 |
|          60,000 |     2.555 s |             777 |

![Minimum support versus runtime](../results/runtime_vs_minsup.png)

Raising support from 15,000 to 60,000 changes runtime from **8.291 to 2.555 seconds**. Counts fall from **9,593 to 777**: fewer groups qualify, so more branches stop early. Less frequent combinations are also lost.

### 3.2 Allotted memory versus runtime

Fixed: **12 dimensions and support 30,000**.

| Memory allowance (MiB) | Median time | Groups written to disk |
| ---------------------: | ----------: | ---------------------: |
|                      8 |     9.701 s |                  1,920 |
|                     16 |     5.592 s |                    370 |
|                     32 |     4.386 s |                     44 |
|                     64 |     4.154 s |                      0 |

![Allotted memory versus runtime](../results/runtime_vs_memory.png)

All settings return **3,921 counts**. Increasing memory from 8 to 64 MiB reduces disk-written groups from **1,920 to 0**, while median time changes from **9.701 to 4.154 seconds**. Larger groups fit in memory, avoiding temporary-file work. Reading and counting still take time.

### 3.3 Number of dimensions versus runtime

Fixed: **support 30,000 and 16 MiB**. Each run uses the first 4, 8, 10 or 12 attributes from the dimension list in Section 2.

| Dimensions | Median time | Counts retained |
| ---------: | ----------: | --------------: |
|          4 |     0.089 s |              36 |
|          8 |     0.704 s |             389 |
|         10 |     2.074 s |           1,244 |
|         12 |     5.423 s |           3,921 |

![Number of dimensions versus runtime](../results/runtime_vs_dimensions.png)

From 4 to 12 dimensions, runtime changes from **0.089 to 5.423 seconds** and output grows from **36 to 3,921 counts**. The number of possible attribute subsets grows from 16 to 4,096. The specific attributes and their distributions also affect the work.

## 4. Optimization technique

### What changes?

Process dimensions with more distinct values first: major industry, education, major occupation, and then the remaining dimensions in that order. This may form smaller groups earlier, allowing BUC to stop below the support threshold sooner. Both versions already use that stopping rule; only the dimension order changes.

### Does it help?

Compare the two in-memory versions on **299,285 records, 12 dimensions and support 30,000**, with three repetitions each. Alternate which version runs first.

| Version                    | Median time | Shortest–longest run | Value groups checked | Counts retained |
| -------------------------- | ----------: | --------------------: | -------------------: | --------------: |
| Original order             |     3.924 s |        3.919–3.948 s |               28,242 |           3,921 |
| More distinct values first |     4.087 s |        4.074–4.113 s |               14,115 |           3,921 |

![Original and reordered BUC runtimes](../results/optimization.png)

Reordering reduces groups checked from **28,242 to 14,115**, about half. Median time changes from **3.924 to 4.087 seconds**. Every reordered run was slower in this experiment, despite checking fewer groups.

Fewer groups need not mean proportionally less time: the number of records sorted in each group also matters. Both reordered implementations preserve every original count.

## 5. Comparison of BUC and AOI

AOI gives a short description of a class. It replaces detailed values with broader groups, so its output is easier to read but depends on the chosen hierarchies. In this analysis, **8.36% of high-income records** belong to the age-35–49, bachelor, professional-and-managerial, private-worker group. AOI is useful when the aim is to describe high-income groups or compare their coverage and high-income share.

BUC keeps the original categories and counts many combinations. At support 30,000, it returns **3,921 counts** across 12 dimensions. For example, the main cube contains **40,154 female high-school graduates**, with no restriction on other attributes. A smaller checked cube contains **4,573 male, bachelor-qualified, high-income records** across all worker classes.

AOI is easier to explain because it deliberately removes detail. Its cost depends on the selected attributes, hierarchies and grouping limits. BUC gives exact counts, but the counts overlap and become harder to inspect as dimensions are added. Its disk version handles limited working memory at the cost of extra file operations.

Use AOI for a compact description of a class. Use BUC when exact counts are needed for several combinations of attributes.

## Files needed to reproduce the work

`question2.ipynb` runs the analysis in order. `aoi.py` contains the shared data loading and AOI code; `buc.py` contains both BUC versions and dimension reordering; `hierarchies.json` stores the grouping rules. `checks.py` holds the independent counting tests and DuckDB reference. Dependencies are listed in `requirements.txt`.

Run the notebooks from `assignments/A2` in this order: `inspect_data.ipynb`, `data_dictionary_mappings_buc.ipynb`, then `question2.ipynb`. The supplied CSV belongs at `M26 DA A2/M26_DA_A2_Part2.csv` and is excluded from submission.

`question2.ipynb` recomputes AOI and BUC results and checks every main-cube count against DuckDB. Saved timing measurements load by default; setting `rerun_timings = True` repeats all timing experiments. The run uses Python 3.10, NumPy 1.26.4, pandas 2.3.3 and DuckDB 1.5.5.

The `results/` folder contains `benchmark_runs.csv` and the four report plots. Timing summaries, mapping checks and example rules are displayed in the notebooks.
