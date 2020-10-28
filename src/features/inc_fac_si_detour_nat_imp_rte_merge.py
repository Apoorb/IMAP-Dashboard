import pandas as pd
import geopandas as gpd
import os
import numpy as np
import seaborn as sns
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
from src.utils import get_project_root

path_to_prj_dir = get_project_root()
path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
path_processed_data = os.path.join(path_to_prj_dir, "data", "processed")
path_inc_fac_si = os.path.join(path_processed_data, "inc_fac_si_scaled.gpkg")
path_to_fig = os.path.join(path_to_prj_dir, "reports", "figures")
path_detour_data = os.path.join(path_processed_data, "detour_testing", "detour_work_ASG.shp")
path_nhs_stc_routes = os.path.join(path_interim_data, "nhs_hpms_stc_routes.csv")
path_if_si_detour_nat_imp = os.path.join(path_processed_data, "if_si_detour_nat_imp.gpkg")
path_interim_sratch = os.path.join(path_interim_data, "scratch")
if not os.path.exists(path_interim_sratch):
    os.mkdir(path_interim_sratch)

if __name__ == "__main__":
    inc_fac_si_gdf = gpd.read_file(path_inc_fac_si, driver="gpkg")
    detour_df = gpd.read_file(path_detour_data, driver="shp")
    nhs_stc_routes = pd.read_csv(path_nhs_stc_routes)
    detour_df_fil = (
        detour_df
        .loc[lambda df: df["class"].astype(int) <= 3]
        .filter(items=["RouteID", "BeginMp", "scr_det", "scr_d90", "scr_nd90"])
        .rename(columns={"RouteID": "route_id", "BeginMp": "aadt_interval_left"})
    )
    if_si_detour_df = (
        inc_fac_si_gdf
        .merge(
            right=detour_df_fil,
            on=["route_id", "aadt_interval_left"],
            how="outer"
        )
    )
    if_si_detour_nat_imp_df = (
        if_si_detour_df
        .merge(
            right=nhs_stc_routes.assign(route_id=lambda df: df.route_id.astype(str)),
            on=["route_id"],
            how="outer"
        )
    )
    if_si_detour_nat_imp_fil_df = (
        if_si_detour_nat_imp_df
        .assign(display_in_imap_tool=lambda df: np.select(
                [
                    df.route_class.isin(["Interstate", "US Route"])
                    | df.stc,
                    ~ df.route_class.isin(["Interstate", "US Route"])
                    & ~ df.stc,
                ],
                [
                    True,
                    False
                ],
                -99).astype(bool)
        )
    )
    if_si_detour_nat_imp_fil_df.to_file(path_if_si_detour_nat_imp, driver="GPKG")
    if_si_detour_nat_imp_fil_df.to_file(os.path.join(path_interim_sratch,
                                                     "if_si_detour_nat_imp.shp"))
    test = if_si_detour_nat_imp_fil_df.loc[if_si_detour_nat_imp_fil_df.scr_det.isna()]
    test2 = if_si_detour_df.loc[if_si_detour_df.route_class.isna()]


