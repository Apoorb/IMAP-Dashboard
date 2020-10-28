# -*- coding: utf-8 -*-
"""
Clean aadt data for all Interstates, US Routes, NC Routes, and secondary route in North
Carolina.
Created by: Apoorba Bibeka
"""
import os
import pandas as pd
from src.utils import get_project_root
from src.utils import read_shp


def add_aadt_new_cols_fix_dtypes(aadt_gdf_):
    """
    Parameters
    ----------
    aadt_gdf_: gpd.GeoDataFrame()
        NCDOT 2018 aadt data layer. Typical the spatial boundaries are at interchanges.
    Returns
    -------
    aadt_df_add_col_: gpd.GeoDataFrame()
        AADT data with new columns for route id, route class, route qual, route inventory
        route number, and route county.
    """
    aadt_df_add_col_ = (
        aadt_gdf_.rename(columns={"begin_mp": "st_mp_pt", "end_mp": "end_mp_pt"})
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
    )
    return aadt_df_add_col_


def test_aadt_df(aadt_gdf_):
    """
    Parameters
    ----------
    aadt_gdf_: gpd.GeoDataFrame()
        NCDOT 2018 aadt data layer. Typical the spatial boundaries are at interchanges.
    Raises
    -------
    AssertionError
        If there is a missing value for either "route_id", "begin_mp", "end_mp",
        or "aadt_2018"
    """
    assert (
        aadt_gdf_[["route_id", "begin_mp", "end_mp", "aadt_2018"]].isna().sum().sum()
        == 0
    ), (
        'Need to remove rows with missing "route_id", "begin_mp", "end_mp", or '
        '"aadt_2018"'
    )
    print("LRS system is complete.")
    try:
        if aadt_gdf_[["geometry"]].isna().sum().sum() != 0:
            raise Exception(
                "NA in geometry column needs to be handled before converting "
                "crs or joining with other dataset."
            )
    except Exception as inst:
        print(inst)


if __name__ == "__main__":
    # Set the paths to relevant files and folders.
    # Load NCDOT 2018 aadt data.
    # ************************************************************************************
    path_to_prj_dir = get_project_root()
    path_to_prj_data = os.path.join(path_to_prj_dir, "data", "raw")
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    aadt_file = os.path.join(
        path_to_prj_data, "NCDOT 2018 Traffic Segments Shapefile Description"
    )
    aadt_gdf = read_shp(aadt_file)
    # Test if there is missing values for AADT data.
    # ************************************************************************************
    test_aadt_df(aadt_gdf)
    # Add new columns on route class, number, county, qual, inventory to the AADT data.
    # ************************************************************************************
    aadt_df_add_col = add_aadt_new_cols_fix_dtypes(aadt_gdf)
    set(aadt_df_add_col.route_no.unique())
    # Filter AADT data to 1: interstate, 2: US Route, 3: NC Route, 4: Secondary Route.
    # ************************************************************************************
    max_highway_class = 3
    aadt_df_fil = aadt_df_add_col.loc[lambda df: df.route_class <= max_highway_class]
    # Filter AADT data to rows with valid geometry. Set CRS to 4326.
    # ************************************************************************************
    aadt_df_fil = aadt_df_fil.loc[lambda df: ~df.geometry.isnull()]
    aadt_df_fil_4326 = aadt_df_fil.to_crs(epsg=4326)
    # Output cleaned AADT data.
    # ************************************************************************************
    out_file_aadt_nc = os.path.join(path_interim_data, "ncdot_2018_aadt.gpkg")
    aadt_df_fil_4326.to_file(out_file_aadt_nc, driver="GPKG")
