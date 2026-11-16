let
    Source = Csv.Document(
        Web.Contents(
            "https://iiithydresearch-my.sharepoint.com/personal/aryaman_bahl_research_iiit_ac_in/Documents/Apps/Microsoft Power Query/Uploaded Files/marketing_campaign 1.csv"
        ),
        [
            Delimiter = "#(tab)",
            Columns = 29,
            QuoteStyle = QuoteStyle.None
        ]
    ),

    #"Promoted headers" =
        Table.PromoteHeaders(
            Source,
            [PromoteAllScalars = true]
        ),

    #"Changed column type" =
        Table.TransformColumnTypes(
            #"Promoted headers",
            {
                {"ID", Int64.Type},
                {"Year_Birth", Int64.Type},
                {"Education", type text},
                {"Marital_Status", type text},
                {"Income", Int64.Type},
                {"Kidhome", Int64.Type},
                {"Teenhome", Int64.Type},
                {"Dt_Customer", type date},
                {"Recency", Int64.Type},
                {"MntWines", Int64.Type},
                {"MntFruits", Int64.Type},
                {"MntMeatProducts", Int64.Type},
                {"MntFishProducts", Int64.Type},
                {"MntSweetProducts", Int64.Type},
                {"MntGoldProds", Int64.Type},
                {"NumDealsPurchases", Int64.Type},
                {"NumWebPurchases", Int64.Type},
                {"NumCatalogPurchases", Int64.Type},
                {"NumStorePurchases", Int64.Type},
                {"NumWebVisitsMonth", Int64.Type},
                {"AcceptedCmp3", Int64.Type},
                {"AcceptedCmp4", Int64.Type},
                {"AcceptedCmp5", Int64.Type},
                {"AcceptedCmp1", Int64.Type},
                {"AcceptedCmp2", Int64.Type},
                {"Complain", Int64.Type},
                {"Z_CostContact", Int64.Type},
                {"Z_Revenue", Int64.Type},
                {"Response", Int64.Type}
            },
            "en-GB"
        ),

    // Count rows with missing Income
    #"Income Missing Count" =
        List.Count(
            List.Select(
                #"Changed column type"[Income],
                each _ = null
            )
        ),

    // Calculate median using non-missing incomes
    #"Income Median" =
        List.Median(
            List.RemoveNulls(
                #"Changed column type"[Income]
            )
        ),

    // Replace only missing Income values
    #"Income Imputed" =
        Table.ReplaceValue(
            #"Changed column type",
            null,
            #"Income Median",
            Replacer.ReplaceValue,
            {"Income"}
        ),

    // STEP 1: Determine the historical reference date
    #"Reference Date" =
        List.Max(
            List.RemoveNulls(
                #"Income Imputed"[Dt_Customer]
            )
        ),

    // STEP 2: Count implausible birth years
    #"Invalid Birth Years" =
        Table.RowCount(
            Table.SelectRows(
                #"Income Imputed",
                each [Year_Birth] = null
                    or [Year_Birth] >
                        Date.Year(#"Reference Date")
                    or [Year_Birth] <
                        Date.Year(#"Reference Date") - 100
            )
        ),

    // STEP 3: Calculate Income quartiles
    #"Income Quartiles" =
        let
            Values =
                List.RemoveNulls(
                    #"Changed column type"[Income]
                ),
            Q1 = List.Percentile(Values, 0.25),
            Q3 = List.Percentile(Values, 0.75)
        in
            [
                Q1 = Q1,
                Q3 = Q3,
                UpperFence = Q3 + 1.5 * (Q3 - Q1)
            ],

    // STEP 4: Count incomes above upper fence
    #"Income Outlier Count" =
        List.Count(
            List.Select(
                List.RemoveNulls(
                    #"Changed column type"[Income]
                ),
                each _ >
                    #"Income Quartiles"[UpperFence]
            )
        ),

    // Create a table containing all audit results
    #"Audit Summary" =
        #table(
            {"Metric", "Result"},
            {
                {
                    "Total customers",
                    Table.RowCount(#"Changed column type")
                },
                {
                    "Missing Income (before cleaning)",
                    #"Income Missing Count"
                },
                {
                    "Income median used for imputation",
                    #"Income Median"
                },
                {
                    "Reference date",
                    #"Reference Date"
                },
                {
                    "Implausible birth years",
                    #"Invalid Birth Years"
                },
                {
                    "Income Q1",
                    #"Income Quartiles"[Q1]
                },
                {
                    "Income Q3",
                    #"Income Quartiles"[Q3]
                },
                {
                    "Income upper outlier threshold",
                    #"Income Quartiles"[UpperFence]
                },
                {
                    "Income outliers above threshold",
                    #"Income Outlier Count"
                },
                {
                    "Unusual marital-status values",
                    Table.RowCount(
                        Table.SelectRows(
                            #"Changed column type",
                            each List.Contains(
                                {"Alone", "Absurd", "YOLO"},
                                [Marital_Status]
                            )
                        )
                    )
                },
                {
                    "Missing Income (after cleaning)",
                    List.Count(
                        List.Select(
                            #"Income Imputed"[Income],
                            each _ = null
                        )
                    )
                }
            }
        ),

    // 1. STANDARDIZE MARITAL STATUS
    #"Clean Marital Status" =
        Table.TransformColumns(
            #"Income Imputed",
            {
                {
                    "Marital_Status",
                    each
                        if _ = "Alone" then "Single"
                        else if List.Contains(
                            {"Absurd", "YOLO"}, _
                        ) then "Unknown"
                        else _,
                    type text
                }
            }
        ),

    // 2. IDENTIFY INVALID BIRTH YEARS
    // Keep original Year_Birth for auditing.
    #"Add Clean Birth Year" =
        Table.AddColumn(
            #"Clean Marital Status",
            "Year_Birth_Clean",
            each
                if [Year_Birth] = null then null
                else if
                    [Year_Birth] <
                    Date.Year(#"Reference Date") - 100
                    or [Year_Birth] >
                    Date.Year(#"Reference Date")
                then null
                else [Year_Birth],
            Int64.Type
        ),

    // 3. FLAG EXTREME INCOMES
    // Retain original Income values.
    #"Flag Income Outliers" =
        Table.AddColumn(
            #"Add Clean Birth Year",
            "Income_Outlier_Flag",
            each
                if [Income] = null then 0
                else if
                    [Income] >
                    #"Income Quartiles"[UpperFence]
                then 1
                else 0,
            Int64.Type
        ),

    // 4. CREATE AGE
    #"Add Age" =
        Table.AddColumn(
            #"Flag Income Outliers",
            "Age",
            each
                if [Year_Birth_Clean] = null
                then null
                else
                    Date.Year(#"Reference Date")
                    - [Year_Birth_Clean],
            Int64.Type
        ),

    // 5. CREATE CUSTOMER TENURE IN DAYS
    #"Add Customer Tenure" =
        Table.AddColumn(
            #"Add Age",
            "Customer_Tenure_Days",
            each
                if [Dt_Customer] = null
                then null
                else
                    Duration.Days(
                        #"Reference Date"
                        - [Dt_Customer]
                    ),
            Int64.Type
        ),

    // 6. CREATE TOTAL SPENDING
    #"Add Total Spending" =
        Table.AddColumn(
            #"Add Customer Tenure",
            "Total_Spending",
            each
                List.Sum({
                    [MntWines],
                    [MntFruits],
                    [MntMeatProducts],
                    [MntFishProducts],
                    [MntSweetProducts],
                    [MntGoldProds]
                }),
            type number
        ),

    // 7. CREATE TOTAL PURCHASES
    // Deal purchases excluded to avoid potential overlap.
    #"Add Total Purchases" =
        Table.AddColumn(
            #"Add Total Spending",
            "Total_Purchases",
            each
                List.Sum({
                    [NumWebPurchases],
                    [NumCatalogPurchases],
                    [NumStorePurchases]
                }),
            Int64.Type
        ),

    // 8. CREATE TOTAL CHILDREN
    #"Add Total Children" =
        Table.AddColumn(
            #"Add Total Purchases",
            "Total_Children",
            each [Kidhome] + [Teenhome],
            Int64.Type
        ),

    // 9. AUTOMATED AUDIT OF ACTUAL CHANGES
    #"Final Audit Summary" =
        Table.Combine({
            #"Audit Summary",
            #table(
                {"Metric", "Result"},
                {
                    {
                        "Marital status values changed",
                        Table.RowCount(
                            Table.SelectRows(
                                #"Income Imputed",
                                each List.Contains(
                                    {"Alone", "Absurd", "YOLO"},
                                    [Marital_Status]
                                )
                            )
                        )
                    },
                    {
                        "Invalid birth years set to null",
                        Table.RowCount(
                            Table.SelectRows(
                                #"Add Clean Birth Year",
                                each [Year_Birth] <> null
                                    and [Year_Birth_Clean] = null
                            )
                        )
                    },
                    {
                        "Income outliers flagged",
                        List.Sum(
                            #"Add Total Children"
                                [Income_Outlier_Flag]
                        )
                    },
                    {
                        "Missing Age after cleaning",
                        List.Count(
                            List.Select(
                                #"Add Total Children"[Age],
                                each _ = null
                            )
                        )
                    },
                    {
                        "Rows after preprocessing",
                        Table.RowCount(
                            #"Add Total Children"
                        )
                    }
                }
            )
        }),

    // 10. FINAL CLEANED DATASET
    #"Customer Data" =
        #"Add Total Children"

in
    #"Customer Data"