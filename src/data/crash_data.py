# -*- coding: utf-8 -*-
import os
import pandas as pd
import geopandas as gpd
from src.utils import get_project_root
from src.data.make_dataset import read_shp


def fix_crash_dat_type(crash_df_, max_highway_class=3):
    """

    Parameters
    ----------
    crash_df_
    max_highway_class

    Returns
    -------

    """
    crash_df_fil_ = (
        crash_df_.assign(
            route_gis=lambda df: df.route_gis.astype(str).str.split(".", expand=True)[
                0
            ],
            route_class=lambda df: df.route_gis.str[0].astype(int),
            route_qual=lambda df: df.route_gis.str[1].astype(int),
            route_inventory=lambda df: df.route_gis.str[2].astype(int),
            route_no=lambda df: df.route_gis.str[3:8].astype(int),
            route_county=lambda df: df.route_gis.str[8:11].astype(int),
            st_end_diff=lambda df: df.end_mp_pt - df.st_mp_pt,
            density_sc=lambda df: pd.to_numeric(df.density_sc, errors="coerce"),
            severity_s=lambda df: pd.to_numeric(df.severity_s, errors="coerce"),
            rate_score=lambda df: pd.to_numeric(df.rate_score, errors="coerce"),
            combined_s=lambda df: pd.to_numeric(df.combined_s, errors="coerce"),
            ka_cnt=lambda df: pd.to_numeric(df.ka_cnt, errors="coerce"),
            bc_cnt=lambda df: pd.to_numeric(df.bc_cnt, errors="coerce"),
            pdo_cnt=lambda df: pd.to_numeric(df.pdo_cnt, errors="coerce"),
            total_cnt=lambda df: pd.to_numeric(df.total_cnt, errors="coerce"),
            shape_len_mi=lambda df: pd.to_numeric(df.shape__len, errors="coerce")
            / 5280,
        )
        .filter(
            items=[
                "route_gis",
                "route_class",
                "route_qual",
                "route_inventory",
                "route_no",
                "route_county",
                "county",
                "st_mp_pt",
                "end_mp_pt",
                "density_sc",
                "severity_s",
                "rate_score",
                "combined_s",
                "combined_r",
                "ka_cnt",
                "bc_cnt",
                "pdo_cnt",
                "total_cnt",
                "shape_len_mi",
                "st_end_diff",
            ]
        )
        .loc[lambda df: df.route_class <= max_highway_class]
    )
    return crash_df_fil_


def test_crash_dat(crash_df_fil_):
    """

    Parameters
    ----------
    crash_df_fil_

    Returns
    -------

    """
    assert (
        crash_df_fil_.route_county == crash_df_fil_.county
    ).all(), "County number in the data does not matches county number from route_gis."


def get_severity_index(
    crash_df_fil_, ka_si_factor=76.8, bc_si_factor=8.4, ou_si_factor=1
):
    crash_df_fil_si_ = crash_df_fil_.assign(
        severity_index=lambda df, ka_si=ka_si_factor, bc_si=bc_si_factor, ou_si=ou_si_factor: (
            ka_si * df.ka_cnt + bc_si * df.bc_cnt + ou_si * df.pdo_cnt
        )
        / df.total_cnt
    )
    return crash_df_fil_si_


if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_to_prj_data = os.path.join(path_to_prj_dir, "data", "raw")
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")

    crash_file = os.path.join(path_to_prj_data, "SectionScores_2015_2019")
    crash_gdf = read_shp(file=crash_file)

    crash_gdf_geom_4326 = crash_gdf.to_crs(epsg=4326).geometry
    crash_df = pd.DataFrame(crash_gdf.drop(columns="geometry"))

    crash_df_fil = fix_crash_dat_type(crash_df)

    test_crash_dat(crash_df_fil)

    crash_df_fil_si = get_severity_index(crash_df_fil)

    crash_df_fil_si_geom = crash_df_fil_si.merge(
        crash_gdf_geom_4326, left_index=True, right_index=True, how="left"
    )
    crash_df_fil_si_geom_gdf = gpd.GeoDataFrame(
        crash_df_fil_si_geom, geometry=crash_df_fil_si_geom.geometry,
    )
    crash_df_fil_si_geom_gdf.crs = "EPSG:4326"
    out_file_crash_si = os.path.join(path_interim_data, "nc_crash_si_2015_2019.gpkg")
    crash_df_fil_si_geom_gdf.to_file(out_file_crash_si, driver="GPKG")
