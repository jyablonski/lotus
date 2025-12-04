import dagster as dg
import polars as pl

sample_data_file = "src/dagster_project/defs/data/sample_data.csv"
processed_data_file = "src/dagster_project/defs/data/processed_data.csv"


@dg.asset
def processed_data():
    ## Read data from the CSV
    df = pl.read_csv(sample_data_file)

    ## Add an age_group column based on the value of age
    df = df.with_columns(
        pl.when(pl.col("age") < 18)
        .then(pl.lit("child"))
        .when((pl.col("age") >= 18) & (pl.col("age") < 65))
        .then(pl.lit("adult"))
        .otherwise(pl.lit("senior"))
        .alias("age_group")
    )

    ## Save processed data
    df.write_csv(processed_data_file)
    return "Data loaded successfully"
