import pandas as pd
import geopandas as gpd
import os
import numpy as np
from src.utils import get_project_root

path_to_prj_dir = get_project_root()
path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
path_processed_data = os.path.join(path_to_prj_dir, "data", "processed")
path_inc_fac_si = os.path.join(path_processed_data, "inc_fac_si_scaled.gpkg")
path_to_fig = os.path.join(path_to_prj_dir, "reports", "figures")
path_detour_data = os.path.join(path_processed_data,
                                "detour_testing",
                                "detour_work_ASG.shp")
path_nhs_stc_routes = os.path.join(path_interim_data, "nhs_hpms_stc_routes.csv")
path_if_si_detour_nat_imp_census_padt = os.path.join(path_processed_data,
                                         "if_si_detour_nat_imp_census_padt.gpkg")
path_padt = os.path.join(path_processed_data,
                                         "padt_on_inc_fac_gis.gpkg")
path_census_growth = os.path.join(path_processed_data,
                                         "census_gpd_growth.gpkg")
path_interim_sratch = os.path.join(path_interim_data, "scratch")
if not os.path.exists(path_interim_sratch):
    os.mkdir(path_interim_sratch)

if __name__ == "__main__":
    inc_fac_si_gdf = gpd.read_file(path_inc_fac_si, driver="gpkg")
    detour_df = gpd.read_file(path_detour_data, driver="shp")
    nhs_stc_routes = pd.read_csv(path_nhs_stc_routes)
    padt_df = gpd.read_file(path_padt, driver="gpkg")
    census_growth_df = gpd.read_file(path_census_growth, driver="gpkg")
    detour_df_fil = (
        detour_df
        .loc[lambda df: df["class"].astype(int) <= 3]
        .filter(items=["RouteID", "BeginMp", "scr_det", "scr_d90", "scr_nd90"])
        .rename(columns={"RouteID": "route_id", "BeginMp": "aadt_interval_left"})
    )
    padt_df_fil = padt_df.filter(items=["route_id", "aadt_interval_left", "padt_rec", "seasonal_fac"])
    census_growth_df_fil = census_growth_df.filter(items=["route_id", "aadt_interval_left",
                                                          "tot_gr_24_yearly",
                                                          "tot_grw_rt_24",
                                                          "GEOID10",
                                                          "tot_flow_2015_24",
                                                          "tot_flow_2040_24",
                                                          "growth_fac"])
    if_si_detour_df = (
        inc_fac_si_gdf
        .merge(
            right=detour_df_fil,
            on=["route_id", "aadt_interval_left"],
            how="left"
        )
    )
    if_si_detour_nat_imp_df = (
        if_si_detour_df
        .merge(
            right=nhs_stc_routes.assign(route_id=lambda df: df.route_id.astype(str)),
            on=["route_id"],
            how="left"
        )
    )
    if_si_detour_nat_imp_fil_df = (
        if_si_detour_nat_imp_df
        .assign(display_in_imap_tool=lambda df: np.select(
                [
                    df.route_class.isin(["Interstate", "US Route"])
                    | df.nat_imp_cat.isin(["nhs", "stc_but_not_nhs"]),
                    ~ df.route_class.isin(["Interstate", "US Route"])
                    & ~ df.nat_imp_cat.isin(["nhs", "stc_but_not_nhs"]),
                ],
                [
                    True,
                    False
                ],
                -99).astype(bool)
        )
    )

    if_si_detour_nat_imp_census_df = (
        if_si_detour_nat_imp_df
        .merge(
            right=census_growth_df_fil.assign(route_id=lambda df: df.route_id.astype(str)),
            on=["route_id", "aadt_interval_left"],
            how="left"
        )
    )

    if_si_detour_nat_imp_census_padt_df = (
        if_si_detour_nat_imp_census_df
        .merge(
            right=padt_df_fil.assign(route_id=lambda df: df.route_id.astype(str)),
            on=["route_id", "aadt_interval_left"],
            how="left"
        )
    )

    if_si_detour_nat_imp_census_padt_df_fil =(
        if_si_detour_nat_imp_census_padt_df
        .filter(
            items=[
                'route_id',
                'route_class',
                'route_qual',
                'route_inventory',
                'route_county',
                'route_no',
                'st_mp_pt_crash',
                'end_mp_pt_crash',
                'st_end_diff_crash',
                'aadt_interval_left',
                'aadt_interval_right',
                'st_end_diff_aadt',
                'seg_len_in_interval',
                'aadt_2018',
                'source',
                'ka_cnt',
                'bc_cnt',
                'pdo_cnt',
                'total_cnt',
                'crash_rate_per_mile_per_year',
                'inc_fac',
                'severity_index_scaled',
                'scr_nd90',
                'nat_imp_fac',
                'growth_fac',
                'seasonal_fac',
                'severity_index',
                'severity_index_q90',
                'scr_det',
                'scr_d90',
                'stc',
                'nhs_net',
                'nat_imp_cat',
                'padt_rec',
                'GEOID10',
                'tot_flow_2040_24',
                'tot_flow_2015_24',
                'tot_gr_24_yearly',
                "tot_grw_rt_24",
                'geometry'
            ]
        )
        .rename(columns={"severity_index_scaled": "si_fac",
                         "scr_nd90": "detour_fac"})
    )

    if_si_detour_nat_imp_census_padt_df_fil.to_file(path_if_si_detour_nat_imp_census_padt, driver="GPKG")
    if_si_detour_nat_imp_census_padt_df_fil.to_file(os.path.join(path_interim_sratch,
                                                     "if_si_detour_nat_imp_census_padt.shp"))

    test = if_si_detour_nat_imp_fil_df.loc[if_si_detour_nat_imp_fil_df.scr_det.isna()]
    test2 = if_si_detour_df.loc[if_si_detour_df.route_class.isna()]


