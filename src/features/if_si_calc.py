"""
Handle missing crash data for incidence factor and severity index calculations.
Created by: Apoorba Bibeka
"""
import pandas as pd
import geopandas as gpd
import os
from src.utils import get_project_root
import sklearn
import numpy as np


if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_processed_data = os.path.join(path_to_prj_dir, "data", "processed")
    path_crash_si = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    path_to_fig = os.path.join(path_to_prj_dir, "reports", "figures")
    path_hpms_2018_nc_fil = os.path.join(
        path_interim_data, "nhs_hpms_2018_routes.csv"
    )
    hpms_2018_nc_fil = pd.read_csv(path_hpms_2018_nc_fil)
    crash_df_fil_si_geom_gdf = gpd.read_file(path_crash_si, driver="gpkg")
    crash_df_fil_si_geom_gdf = crash_df_fil_si_geom_gdf.assign(
        route_class=lambda df: df.route_class.replace(
            {1: "Interstate", 2: "US Route", 3: "NC Route", 4: "Secondary Routes"}
        )).query("route_class in ['Interstate', 'US Route', 'NC Route']")
    crash_df_fil_si_geom_gdf_no_nan = crash_df_fil_si_geom_gdf.query(
        "~ severity_index.isna()"
    )
    crash_df_fil_si_geom_gdf.groupby("route_class").severity_index.quantile(.95)
    crash_df_fil_si_geom_gdf_no_nan.severity_index.describe()
    quantile_90th = crash_df_fil_si_geom_gdf.severity_index.quantile(.90)

    crash_df_fil_si_geom_gdf_no_nan_scaled_si = crash_df_fil_si_geom_gdf_no_nan.assign(
        severity_index_need_scaling=lambda df: np.select(
            [df.severity_index <= quantile_90th,
             df.severity_index > quantile_90th],
            [True, False]
        ),
        severity_index_scaled=lambda df: (
            df.groupby("severity_index_need_scaling")
            .severity_index
            .transform(lambda x: sklearn.preprocessing.minmax_scale(x,
                                                                    (1, 1.2)
                                                                    )
                       )
        ),
    )
    crash_df_fil_si_geom_gdf_no_nan_scaled_si.loc[
        lambda x: ~ x.severity_index_need_scaling.astype(bool),
        "severity_index_scaled"
        ] = 1.2

    path_si_scaled_shp_dir = os.path.join(path_processed_data, "si_scaled")
    if not os.path.isdir(path_si_scaled_shp_dir):
        os.mkdir(path_si_scaled_shp_dir)
    path_si_scaled_shp = os.path.join(path_si_scaled_shp_dir, "si_scaled.shp")

    crash_df_fil_si_geom_gdf_no_nan_scaled_si.to_file(path_si_scaled_shp)