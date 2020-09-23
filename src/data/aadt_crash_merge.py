# -*- coding: utf-8 -*-
"""
Merge AADT and Crash data for all Interstates, US Routes, and NC Routes in North Carolina.
Created by: Apoorba Bibeka
"""
import os
import pandas as pd
import geopandas as gpd
from src.utils import get_project_root
from src.utils import reorder_columns
import numpy as np
from src.data.crash import get_severity_index


def merge_aadt_crash(aadt_gdf_, crash_gdf_, quiet=True):
    """
    Function for merging AADT and Crash data.
    Parameters
    ----------
    aadt_gdf_ : gpd.GeoDataFrame()
        AADT data.
    crash_gdf_: gpd.GeoDataFrame()
        Crash data.
    quiet: bool
        False, for debug mode.
    Returns
    -------
    aadt_crash_gdf_ : gpd.GeoDataFrame()
        Merged AADT and Crash data with Crash data dissolved based on AADT intervals.
    aadt_but_no_crash_route_set : set
        Set of route IDs with AADT data that doesn't have associated crash data.
    """
    # Group data by route #, county, route qual.
    aadt_grp = aadt_gdf_.groupby(["route_id"])
    crash_grp = crash_gdf_.groupby(["route_gis"])
    aadt_grp_keys = aadt_gdf_.groupby(["route_id"]).groups.keys()

    aadt_grp_sub_dict = {}
    crash_grp_sub_dict = {}
    aadt_but_no_crash_route_list_ = list()
    for aadt_grp_key in aadt_grp_keys:
        aadt_grp_sub = aadt_grp.get_group(aadt_grp_key).copy()
        if not quiet:
            print(
                f"Now processing route {aadt_grp_key}; {aadt_grp_sub[['route_class','route_qual', 'route_no', 'route_county']].head(1)}"
            )
        try:
            crash_grp_sub = crash_grp.get_group(aadt_grp_key).copy()
        except KeyError as err:
            print(f"No Crash data for route {err.args}")
            aadt_but_no_crash_route_list_.append(aadt_grp_key)
            continue

        # Bin the crash start milepost and end milepost based on AADT.
        aadt_crash_df_bin = bin_aadt_crash(
            aadt_grp_sub_=aadt_grp_sub, crash_grp_sub_=crash_grp_sub,
        )
        aadt_grp_sub_dict[aadt_grp_key] = aadt_crash_df_bin["aadt_grp_sub"]
        crash_grp_sub_dict[aadt_grp_key] = aadt_crash_df_bin[
            "crash_grp_sub_aadt_interval_long"]

    aadt_gdf_1 = pd.concat(aadt_grp_sub_dict.values()).sort_values(
        ["route_id", "st_mp_pt"]
    )

    # Subset crash dataset with non-zero rows.
    crash_grp_sub_no_empty_df_set = list(crash_grp_sub_dict.values())
    if min([len(values) for values in crash_grp_sub_dict.values()]) == 0:
        crash_grp_sub_no_empty_df_set = [
            value for value in crash_grp_sub_dict.values() if len(value) != 0
        ]

    for key, value in crash_grp_sub_dict.items():
        if len(value) == 0:
            aadt_but_no_crash_route_list_.append(key)

    crash_gdf_1 = pd.concat(crash_grp_sub_no_empty_df_set)

    # Subset to relevant columns.
    crash_gdf_no_duplicates = (
        crash_gdf_1.loc[
            :,
            [
                "route_gis",
                "aadt_interval",
                "ka_cnt",
                "bc_cnt",
                "pdo_cnt",
                "total_cnt",
                "st_mp_pt",
                "end_mp_pt",
                "shape_len_mi",
                "st_end_diff",
                "geometry",
            ],
        ]
        .drop_duplicates(["route_gis", "aadt_interval", "st_mp_pt"])
        .sort_values(["route_gis", "st_mp_pt"])
    )

    # Change the crash freqency in a segment based on the AADT interval length and
    # position. Consider crashes to be uniform distributed along the length.
    crash_gdf_adj_crash_by_len = scale_crash_by_seg_len(crash_gdf_no_duplicates)
    # Aggregate crash fields based on AADT intervals.
    # dissolve() is the groupby implementation with spatial attributes (geometry column)
    crash_gdf_adj_crash_by_len_dissolve = crash_gdf_adj_crash_by_len.dissolve(
        by=["route_gis", "aadt_interval"],
        aggfunc={
            "ka_cnt": "sum",
            "bc_cnt": "sum",
            "pdo_cnt": "sum",
            "total_cnt": "sum",
            "st_mp_pt": "min",
            "end_mp_pt": "max",
            "st_end_diff": "sum",
            "aadt_interval_left": "first",
            "aadt_interval_right": "first",
            "seg_len_in_interval": "sum",
        },
    ).reset_index()
    crash_gdf_adj_crash_by_len_dissolve = get_severity_index(
        crash_gdf_adj_crash_by_len_dissolve
    )
    crash_gdf_adj_crash_by_len_dissolve = crash_gdf_adj_crash_by_len_dissolve.assign(
        crash_rate_per_mile=lambda df: df.total_cnt / df.seg_len_in_interval
    )
    aadt_crash_df_ = (
        aadt_gdf_1.merge(
            crash_gdf_adj_crash_by_len_dissolve,
            left_on=["route_id", "aadt_interval"],
            right_on=["route_gis", "aadt_interval"],
            suffixes=["_aadt", "_crash"],
            how="left",
        )
        .filter(
            items=[
                "route_id",
                "route_class",
                "route_qual",
                "route_inventory",
                "route_county",
                "route_no",
                "st_mp_pt_crash",
                "end_mp_pt_crash",
                "st_end_diff_crash",
                "aadt_interval_left",
                "aadt_interval_right",
                "st_end_diff_aadt",
                "seg_len_in_interval",
                "aadt_2018",
                "source",
                "ka_cnt",
                "bc_cnt",
                "pdo_cnt",
                "total_cnt",
                "severity_index",
                "crash_rate_per_mile",
                "geometry_aadt",
            ]
        )
        .sort_values(["route_id", "aadt_interval_left"])
    )
    aadt_crash_gdf_ = gpd.GeoDataFrame(aadt_crash_df_, geometry="geometry_aadt")
    aadt_crash_gdf_.crs = "EPSG:4326"

    aadt_but_no_crash_route_set_ = set(aadt_but_no_crash_route_list_)
    return aadt_crash_gdf_, aadt_but_no_crash_route_set_


def bin_aadt_crash(aadt_grp_sub_, crash_grp_sub_):
    """

    Parameters
    ----------
    aadt_grp_sub_
    crash_grp_sub_st_
    crash_grp_sub_end_

    Returns
    -------

    """
    # Create bins for grouping the data
    aadt_grp_sub_ = aadt_grp_sub_.sort_values(["st_mp_pt"]).assign(
        st_mp_pt_shift1=lambda df: df.st_mp_pt.shift(-1).fillna(df.end_mp_pt),
        overlapping_interval=lambda df: (df.st_mp_pt_shift1 - df.end_mp_pt).lt(0),
        end_mp_pt_cor=lambda df: df[["end_mp_pt", "st_mp_pt_shift1"]].min(axis=1),
        st_end_diff=lambda df: df.end_mp_pt - df.st_mp_pt,
    )
    if aadt_grp_sub_.overlapping_interval.any():
        print(
            f"Fixing issue with overlapping interval in "
            f"route {aadt_grp_sub_[['route_class', 'route_qual', 'route_no', 'route_county']].head(1)}"
            f" for the following rows: \n"
            f"{aadt_grp_sub_.loc[aadt_grp_sub_.overlapping_interval, ['st_mp_pt', 'end_mp_pt', 'st_mp_pt_shift1', 'end_mp_pt_cor']]}"
        )

    aadt_lrs_bins = pd.IntervalIndex.from_arrays(
        aadt_grp_sub_.st_mp_pt, aadt_grp_sub_.end_mp_pt_cor, closed="left"
    )
    aadt_grp_sub_.loc[:, "aadt_interval"] = aadt_lrs_bins

    crash_grp_sub_aadt_interval_ = crash_grp_sub_.copy()
    crash_grp_sub_aadt_interval_ = (
        crash_grp_sub_aadt_interval_.assign(
            crash_interval=lambda df: pd.IntervalIndex.from_arrays(
                df.st_mp_pt, df.end_mp_pt, closed="left"
            ),
            aadt_interval_list=lambda df: df.crash_interval.apply(
                lambda x: [
                    interval for interval in aadt_lrs_bins if x.overlaps(interval)
                ]
            ),
        )
        .drop(columns=["crash_interval"])
        .sort_values(["route_gis", "st_mp_pt"])
    )

    crash_grp_sub_aadt_interval_long_= (
        crash_grp_sub_aadt_interval_.aadt_interval_list
     .apply(pd.Series)
     .merge(
        crash_grp_sub_aadt_interval_[["route_gis", "st_mp_pt", "aadt_interval_list"]],
        left_index=True,
        right_index=True)
     .drop(["aadt_interval_list"], axis=1)
     .melt(id_vars = ["route_gis", "st_mp_pt"], value_name="aadt_interval")
     .drop("variable", axis=1)
     .dropna())

    crash_grp_sub_aadt_interval_long_ = (
        crash_grp_sub_aadt_interval_.drop(columns = "aadt_interval_list")
        .merge(
            crash_grp_sub_aadt_interval_long_,
            on = ["route_gis", "st_mp_pt"],
            how = "left"
        ))

    crash_grp_sub_aadt_interval_long_ = reorder_columns(
        df=crash_grp_sub_aadt_interval_long_,
        first_cols=[
            "route_gis",
            "route_class",
            "route_qual",
            "route_inventory",
            "route_no",
            "route_county",
            "aadt_interval",
            "st_mp_pt",
            "end_mp_pt",
        ],
    )
    return {
        "aadt_grp_sub": aadt_grp_sub_,
        "crash_grp_sub_aadt_interval_long": crash_grp_sub_aadt_interval_long_,
    }


def scale_crash_by_seg_len(crash_gdf_2_):
    """
    Consider the crashes to be uniformly distributed along the crash segment.
    Scale the crashes based on the length of the crash segment and position of
    crash segment w.r.t AADT segment.
    Parameters
    ----------
    crash_gdf_2_ : gpd.GeoDataFrame
        Crash data with AADT bins.
    Returns
    -------
    crash_gdf_2_adj_crash_freq_by_len_ : crash_gdf_2_ with crash frequency adjusted based
    on the length of the crash segment and position of crash segment w.r.t AADT segment.
    """
    crash_gdf_2_adj_crash_freq_by_len_ = (
        crash_gdf_2_.assign(
            aadt_interval_left=lambda df: pd.IntervalIndex(df.aadt_interval).left,
            aadt_interval_right=lambda df: pd.IntervalIndex(df.aadt_interval).right,
            crash_seg_cat=lambda df: np.select(
                [
                    (df.st_mp_pt < df.aadt_interval_left)
                    & (df.end_mp_pt <= df.aadt_interval_right),
                    (df.st_mp_pt < df.aadt_interval_left)
                    & (df.end_mp_pt > df.aadt_interval_right),
                    (df.st_mp_pt >= df.aadt_interval_left)
                    & (df.end_mp_pt <= df.aadt_interval_right),
                    (df.st_mp_pt >= df.aadt_interval_left)
                    & (df.end_mp_pt > df.aadt_interval_right),
                ],
                [
                    "left_extra_len",
                    "left_right_extra_len",
                    "no_extra_len",
                    "right_extra_len",
                ],
                "error",
            ),
            seg_len_in_interval=lambda df: np.select(
                [
                    df.crash_seg_cat == "left_extra_len",
                    df.crash_seg_cat == "left_right_extra_len",
                    df.crash_seg_cat == "no_extra_len",
                    df.crash_seg_cat == "right_extra_len",
                ],
                [
                    df.st_end_diff - (df.aadt_interval_left - df.st_mp_pt),
                    df.aadt_interval_right - df.aadt_interval_left,
                    df.st_end_diff,
                    df.st_end_diff - (df.end_mp_pt - df.aadt_interval_right),
                ],
                np.nan,
            ),
            ratio_len_in_interval=lambda df: df.seg_len_in_interval / df.st_end_diff,
            ka_cnt=lambda df: df.ratio_len_in_interval * df.ka_cnt,
            bc_cnt=lambda df: df.ratio_len_in_interval * df.bc_cnt,
            pdo_cnt=lambda df: df.ratio_len_in_interval * df.pdo_cnt,
            total_cnt=lambda df: df.ratio_len_in_interval * df.total_cnt,
        )
        .drop(columns=["shape_len_mi"])
        .filter(
            items=[
                "route_gis",
                "aadt_interval",
                "ka_cnt",
                "bc_cnt",
                "pdo_cnt",
                "total_cnt",
                "st_mp_pt",
                "end_mp_pt",
                "shape_len_mi",
                "st_end_diff",
                "aadt_interval_left",
                "aadt_interval_right",
                "crash_seg_cat",
                "seg_len_in_interval",
                "ratio_len_in_interval",
                "geometry",
            ]
        )
    )
    return crash_gdf_2_adj_crash_freq_by_len_


def get_missing_aadt_gdf(aadt_gdf__, aadt_but_no_crash_route_set__):
    return aadt_gdf__.query("route_id in @aadt_but_no_crash_route_set__")


def get_missing_crash_gdf(crash_gdf__, aadt_but_no_crash_route_set__):
    return crash_gdf__.query("route_gis in @aadt_but_no_crash_route_set__")


if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_crash_si = os.path.join(path_interim_data, "nc_crash_si_2015_2019.gpkg")
    path_aadt_nc = os.path.join(path_interim_data, "ncdot_2018_aadt.gpkg")
    crash_gdf = gpd.read_file(path_crash_si, driver="gpkg")
    aadt_gdf = gpd.read_file(path_aadt_nc, driver="gpkg")
    aadt_gdf = aadt_gdf.query("route_class in [1, 2, 3]")
    crash_gdf = crash_gdf.query("route_class in [1, 2, 3]")
    crash_gdf_95_40 = crash_gdf.query("route_no in [40, 95]")
    aadt_gdf_95_40 = aadt_gdf.query("route_no in [40, 95]")

    aadt_crash_gdf, aadt_but_no_crash_route_set = merge_aadt_crash(
        aadt_gdf_=aadt_gdf.query("route_id == '20000129020'"), crash_gdf_=crash_gdf, quiet=True
    )

    aadt_crash_gdf_40_95, aadt_but_no_crash_route_set_40_95 = merge_aadt_crash(
        aadt_gdf_=aadt_gdf_95_40, crash_gdf_=crash_gdf_95_40, quiet=True
    )
    aadt_crash_gdf, aadt_but_no_crash_route_set = merge_aadt_crash(
        aadt_gdf_=aadt_gdf, crash_gdf_=crash_gdf, quiet=True
    )
    out_file_aadt_crash = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    aadt_crash_gdf.to_file(out_file_aadt_crash, driver="GPKG")

    failed_merge_aadt_dat = get_missing_aadt_gdf(
        aadt_gdf, aadt_but_no_crash_route_set
    ).sort_values(["route_id", "st_mp_pt"])
    failed_merge_crash_dat = get_missing_crash_gdf(
        crash_gdf, aadt_but_no_crash_route_set
    ).sort_values(["route_gis", "st_mp_pt"])
    out_file_aadt_but_no_crash_route_set = os.path.join(
        path_interim_data, "aadt_but_no_crash_route_set.csv"
    )
    out_file_aadt_but_no_crash_route_set.to_csv(out_file_aadt_but_no_crash_route_set)
