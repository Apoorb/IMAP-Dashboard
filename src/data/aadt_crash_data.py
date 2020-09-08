# -*- coding: utf-8 -*-
import os
import pandas as pd
import geopandas as gpd
from src.utils import get_project_root
import numpy as np
from src.data.crash_data import get_severity_index

def merge_aadt_crash(aadt_gdf_, crash_gdf_):
    """
    Function for merging AADT and Crash data.
    Parameters
    ----------
    aadt_gdf_ : gpd.GeoDataFrame()
        AADT data.
    crash_gdf_: gpd.GeoDataFrame()
        Crash data.
    Returns
    -------
    aadt_crash_gdf_ : gpd.GeoDataFrame()
        Merged AADT and Crash data with Crash data dissolved based on AADT intervals.
    """
    # Cut the data and create a column with diff bins :
    aadt_grp = aadt_gdf_.groupby(["route_id"])
    crash_grp = crash_gdf_.groupby(["route_gis"])
    aadt_grp_keys = aadt_gdf_.groupby(["route_id"]).groups.keys()

    aadt_grp_sub_list = []
    crash_grp_sub_list = []
    for aadt_grp_key in aadt_grp_keys:
        aadt_grp_sub = aadt_grp.get_group(aadt_grp_key).copy()
        crash_grp_sub_st = crash_grp.get_group(aadt_grp_key).copy()
        crash_grp_sub_end = crash_grp.get_group(aadt_grp_key).copy()
        # Create bins for grouping the data
        aadt_lrs_bins = pd.IntervalIndex.from_arrays(
            aadt_grp_sub.st_mp_pt, aadt_grp_sub.end_mp_pt, closed="left"
        )
        aadt_grp_sub.loc[:, "aadt_interval"] = aadt_lrs_bins
        crash_grp_sub_st.loc[:, "aadt_interval"] = pd.cut(
            crash_grp_sub_st["st_mp_pt"], aadt_lrs_bins
        )
        crash_grp_sub_end.loc[:, "aadt_interval"] = pd.cut(
            crash_grp_sub_st["end_mp_pt"], aadt_lrs_bins
        )
        crash_grp_sub_end = crash_grp_sub_end.loc[lambda df: ~df.aadt_interval.isna()]
        aadt_grp_sub_list.append(aadt_grp_sub)
        crash_grp_sub_list.append(crash_grp_sub_st)
        crash_grp_sub_list.append(crash_grp_sub_end)
    aadt_gdf_1 = pd.concat(aadt_grp_sub_list).sort_values(["route_id", "st_mp_pt"])
    crash_gdf_1 = pd.concat(crash_grp_sub_list)
    crash_gdf_2 = (
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
    crash_gdf_2_process = scale_crash_by_seg_len(crash_gdf_2)
    # dissolve() is the groupby implementation with spatial attributes (geometry column)
    crash_gdf_2_process_dissolve = crash_gdf_2_process.dissolve(
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
    crash_gdf_2_process_dissolve = get_severity_index(crash_gdf_2_process_dissolve)
    crash_gdf_2_process_dissolve = crash_gdf_2_process_dissolve.assign(
        crash_rate_per_mile = lambda df: df.total_cnt / df.seg_len_in_interval
    )
    aadt_crash_df_ = (
        aadt_gdf_1.merge(
            crash_gdf_2_process_dissolve,
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
    aadt_crash_gdf_ = gpd.GeoDataFrame(aadt_crash_df_,
                                       geometry="geometry_aadt")
    aadt_crash_gdf_.crs = "EPSG:4326"
    return aadt_crash_gdf_


def scale_crash_by_seg_len(crash_gdf_2_):
    crash_gdf_2_process_ = (
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
                    df.aadt_interval_left - df.aadt_interval_right,
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
                "geometry",
            ]
        )
    )
    return crash_gdf_2_process_


if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_crash_si = os.path.join(path_interim_data, "nc_crash_si_2015_2019.gpkg")
    path_aadt_nc = os.path.join(path_interim_data, "ncdot_2018_aadt.gpkg")
    crash_gdf = gpd.read_file(path_crash_si, driver="gpkg")
    aadt_gdf = gpd.read_file(path_aadt_nc, driver="gpkg")
    crash_gdf_95_40 = crash_gdf.query("route_no in [40, 95]")
    aadt_gdf_95_40 = aadt_gdf.query("route_no in [40, 95]")


    aadt_crash_gdf_40_95 = merge_aadt_crash(
        aadt_gdf_=aadt_gdf_95_40,
        crash_gdf_=crash_gdf_95_40,
    )

    out_file_aadt_crash = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    aadt_crash_gdf_40_95.to_file(out_file_aadt_crash, driver="GPKG")



