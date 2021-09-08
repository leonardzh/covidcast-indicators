# -*- coding: utf-8 -*-
"""Functions for pulling data from the CDC data website for vaccines."""
import hashlib
from logging import Logger
from delphi_utils.geomap import GeoMapper
import numpy as np
import pandas as pd





def pull_cdcvacc_data(base_url: str, logger: Logger) -> pd.DataFrame:
    """Pull the latest data from the CDC on vaccines and conform it into a dataset.

    The output dataset has:
    - Each row corresponds to (County, Date), denoted (FIPS, timestamp)
    - Each row additionally has columns that correspond to the counts or
      cumulative counts of vaccination status (fully vaccinated,
      partially vaccinated) of various age groups (all, 12+, 18+, 65+)
      from December 13th 2020 until the latest date

    Note that the raw dataset gives the `cumulative` metrics, from which
    we compute `counts` by taking first differences.  Hence, `counts`
    may be negative.  This is wholly dependent on the quality of the raw
    dataset.

    We filter the data such that we only keep rows with valid FIPS, or "FIPS"
    codes defined under the exceptions of the README.  The current  exceptions
    include:
    # - 0: statewise unallocated
    Parameters
    ----------
    base_url: str
        Base URL for pulling the CDC Vaccination Data
    logger: Logger
    Returns
    -------
    pd.DataFrame
        Dataframe as described above.
    """
    # Columns to drop the the data frame.
    drop_columns = [
    "date",
    "recip_state",
    "series_complete_pop_pct",
    "mmwr_week",
    "recip_county",
    "state_id"
    ]


    # Read data
    df = pd.read_csv(base_url)
    logger.info("data retrieved from source",
                num_rows=df.shape[0],
                num_cols=df.shape[1],
                min_date=min(df['Date']),
                max_date=max(df['Date']),
                checksum=hashlib.sha256(pd.util.hash_pandas_object(df).values).hexdigest())
    df.columns = [i.lower() for i in df.columns]

    df['recip_state'] = df['recip_state'].str.lower()
    drop_columns.extend([x for x in df.columns if ("pct" in x) | ("svi" in x)])
    drop_columns =  list(set(drop_columns))
    df = GeoMapper().add_geocode(df, "state_id", "state_code",
        from_col="recip_state", new_col="state_id", dropna=False)
    df['state_id'] = df['state_id'].fillna('0').astype(int)
    # Change FIPS from 0 to XX000 for statewise unallocated cases/deaths
    unassigned_index = (df["fips"] == "UNK")
    df.loc[unassigned_index, "fips"] = df["state_id"].loc[unassigned_index].values * 1000

    # Conform FIPS
    df["fips"] = df["fips"].apply(lambda x: f"{int(x):05d}")
    df["timestamp"] = pd.to_datetime(df["date"])
    # Drop unnecessary columns (state is pre-encoded in fips)
    try:
        df.drop(drop_columns, axis=1, inplace=True)
    except KeyError as e:
        raise ValueError(
            "Tried to drop non-existent columns. The dataset "
            "schema may have changed.  Please investigate and "
            "amend drop_columns."
        ) from e
    # timestamp: str -> datetime
    df.columns = ["fips",
                  "cumulative_counts_tot_vaccine",
                  "cumulative_counts_tot_vaccine_12P",
                  "cumulative_counts_tot_vaccine_18P",
                  "cumulative_counts_tot_vaccine_65P",
                  "cumulative_counts_part_vaccine",
                  "cumulative_counts_part_vaccine_12P",
                  "cumulative_counts_part_vaccine_18P",
                  "cumulative_counts_part_vaccine_65P",
                  "timestamp"]
    df_dummy = df.loc[(df["fips"]!='00000') & (df["timestamp"] == min(df["timestamp"]))].copy()
    #handle fips 00000 separately
    df_oth = df.loc[((df["fips"]=='00000') &
        (df["timestamp"]==min(df[df['fips'] == '00000']['timestamp'])))].copy()
    df_dummy = pd.concat([df_dummy, df_oth])
    df_dummy.loc[:, "timestamp"] = df_dummy.loc[:, "timestamp"] - pd.Timedelta(days=1)
    df_dummy.loc[:, ["cumulative_counts_tot_vaccine",
                    "cumulative_counts_tot_vaccine_12P",
                    "cumulative_counts_tot_vaccine_18P",
                    "cumulative_counts_tot_vaccine_65P",
                    "cumulative_counts_part_vaccine",
                    "cumulative_counts_part_vaccine_12P",
                    "cumulative_counts_part_vaccine_18P",
                    "cumulative_counts_part_vaccine_65P",
                    ]] = 0

    df =pd.concat([df_dummy, df])
    # Obtain new_counts
    df.sort_values(["fips", "timestamp"], inplace=True)
    df["counts_tot_vaccine"] = df["cumulative_counts_tot_vaccine"].diff()  # 1st discrete difference
    df["counts_tot_vaccine_12P"] = df["cumulative_counts_tot_vaccine_12P"].diff()
    df["counts_tot_vaccine_18P"] = df["cumulative_counts_tot_vaccine_18P"].diff()
    df["counts_tot_vaccine_65P"] = df["cumulative_counts_tot_vaccine_65P"].diff()
    df["counts_part_vaccine"] = df["cumulative_counts_part_vaccine"].diff()
    df["counts_part_vaccine_12P"] = df["cumulative_counts_part_vaccine_12P"].diff()
    df["counts_part_vaccine_18P"] = df["cumulative_counts_part_vaccine_18P"].diff()
    df["counts_part_vaccine_65P"] = df["cumulative_counts_part_vaccine_65P"].diff()

    rem_list = [ x for x in list(df.columns) if x not in ['timestamp', 'fips'] ]
    # Handle edge cases where we diffed across fips
    mask = df["fips"] != df["fips"].shift(1)
    df.loc[mask, rem_list] = np.nan
    print(rem_list)
    df.reset_index(inplace=True, drop=True)
    # Final sanity checks
    unique_days = df["timestamp"].unique()
    min_timestamp = min(unique_days)
    max_timestamp = max(unique_days)
    n_days = (max_timestamp - min_timestamp) / np.timedelta64(1, "D") + 1
    if n_days != len(unique_days):
        raise ValueError(
            f"Not every day between {min_timestamp} and "
            "{max_timestamp} is represented."
        )
    return df.loc[
        df["timestamp"] >= min(df["timestamp"]),
        [  # Reorder
            "fips",
            "timestamp",
            "cumulative_counts_tot_vaccine",
            "counts_tot_vaccine",
            "cumulative_counts_tot_vaccine_12P",
            "counts_tot_vaccine_12P",
            "cumulative_counts_tot_vaccine_18P",
            "counts_tot_vaccine_18P",
            "cumulative_counts_tot_vaccine_65P",
            "counts_tot_vaccine_65P",
            "cumulative_counts_part_vaccine",
            "counts_part_vaccine",
            "cumulative_counts_part_vaccine_12P",
            "counts_part_vaccine_12P",
            "cumulative_counts_part_vaccine_18P",
            "counts_part_vaccine_18P",
            "cumulative_counts_part_vaccine_65P",
            "counts_part_vaccine_65P"
        ],
    ].reset_index(drop=True)
