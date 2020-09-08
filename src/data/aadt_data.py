# -*- coding: utf-8 -*-
import os
import pandas as pd
import geopandas as gpd
from src.utils import get_project_root
from src.data.make_dataset import read_shp


def fix_aadt_df_type(aadt_df_, max_highway_class=3):
    """

    Parameters
    ----------
    aadt_df_
    max_highway_class

    Returns
    -------
    aadt_df_fil_
    """
    aadt_df_fil_ = (
        aadt_df_.rename(columns={"begin_mp": "st_mp_pt", "end_mp": "end_mp_pt"})
        .assign(
            route_id=lambda df: df.route_id.astype(str).str.split(".", expand=True)[0],
            route_class=lambda df: df.route_id.str[0].astype(int),
            route_qual=lambda df: df.route_id.str[1].astype(int),
            route_inventory=lambda df: df.route_id.str[2].astype(int),
            route_no=lambda df: df.route_id.str[3:8].astype(int),
            route_county=lambda df: df.route_id.str[8:11].astype(int),
            st_end_diff=lambda df: df.end_mp_pt - df.st_mp_pt,
            aadt_2018=lambda df: pd.to_numeric(df.aadt_2018, errors="raise"),
            source=lambda df: df.source.astype(str),
        )
        .filter(
            items=[
                "route_id",
                "route_class",
                "route_qual",
                "route_inventory",
                "route_no",
                "route_county",
                "county",
                "st_mp_pt",
                "end_mp_pt",
                "st_end_diff",
                "aadt_2018",
                "source",
                "geometry",
            ]
        )
        .loc[lambda df: df.route_class <= max_highway_class]
    )
    return aadt_df_fil_


def test_aadt_df(aadt_df_):
    assert (
        aadt_df_[["route_id", "begin_mp", "end_mp", "aadt_2018"]].isna().sum().sum()
        == 0
    ), (
        'Need to remove rows with missing "route_id", "begin_mp", "end_mp", or '
        '"aadt_2018"'
    )
    print("LRS system is complete.")
    try:
        if aadt_df_[["geometry"]].isna().sum().sum() != 0:
            raise Exception(
                "NA in geometry column needs to be handled before converting "
                "crs or joining with other dataset."
            )
    except Exception as inst:
        print(inst)


if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_to_prj_data = os.path.join(path_to_prj_dir, "data", "raw")
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    aadt_file = os.path.join(
        path_to_prj_data, "NCDOT 2018 Traffic Segments Shapefile Description"
    )
    aadt_gdf = read_shp(aadt_file)
    test_aadt_df(aadt_gdf)
    aadt_df_fil = fix_aadt_df_type(aadt_gdf)
    aadt_df_fil = aadt_df_fil.loc[lambda df: ~ df.geometry.isnull()]
    aadt_df_fil_4326 = aadt_df_fil.to_crs(epsg=4326)

    out_file_aadt_nc = os.path.join(path_interim_data, "ncdot_2018_aadt.gpkg")
    aadt_df_fil_4326.to_file(out_file_aadt_nc, driver="GPKG")
