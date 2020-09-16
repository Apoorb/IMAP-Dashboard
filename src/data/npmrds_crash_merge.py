# -*- coding: utf-8 -*-
import os
import pandas as pd
import geopandas as gpd
from src.utils import get_project_root


if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_crash_si = os.path.join(path_interim_data, "nc_crash_si_2015_2019.gpkg")
    path_npmrds_nc = os.path.join(path_interim_data, "npmrds_nc_2019.gpkg")
    crash_gdf = gpd.read_file(path_crash_si, driver="gpkg")
    npmrds_gdf = gpd.read_file(path_npmrds_nc, driver="gpkg")
    crash_gdf_95 = crash_gdf.query("route_no == 95")
    npmrds_gdf_95 = npmrds_gdf.query("route_numb == 95").filter(
        items=[
            "route_numb",
            "tmc",
            "tmc_linear",
            "county",
            "tmc_type",
            "direction",
            "route_qual",
            "geometry",
        ]
    )
    test = gpd.sjoin(crash_gdf_95, npmrds_gdf_95, how="inner", op="intersects")
    test = test.sort_values(["route_no", "route_county", "st_mp_pt"])
