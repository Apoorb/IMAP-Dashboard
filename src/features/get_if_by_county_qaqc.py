import pandas as pd
import geopandas as gpd
import os
import re
from src.utils import get_project_root
from src.data.crash import get_severity_index
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
from plotly.offline import plot
pio.renderers.default = "browser"

path_to_prj_dir = get_project_root()
path_to_raw = os.path.join(path_to_prj_dir, "data", "raw")
path_processed_data = os.path.join(path_to_prj_dir, "data", "processed")
path_if_si_detour_nat_imp = os.path.join(path_processed_data,
                                         "if_si_detour_nat_imp.gpkg")
path_to_county = os.path.join(
    path_to_raw,
    "CountyBoundary_SHP",
    "BoundaryCountyPolygon.shp",
)
path_to_nathan_inc_fac = os.path.join(
    path_to_raw,
    "nathan_inc_fac.xlsx"
)

if __name__ == "__main__":
    if_process_df = gpd.read_file(path_if_si_detour_nat_imp, driver="gpkg")
    county_df = gpd.read_file(path_to_county, driver="shp")
    county_df_fil = (
        county_df
        .filter(items=["FIPS", "CountyName", "SapCountyI"])
        .rename(columns={
            "FIPS": "fips", "CountyName": "county_nm", "SapCountyI": "sap_county_id"})
        .assign(
            sap_county_id=lambda df: df.sap_county_id.astype(int),
            county_nm=lambda df: df.county_nm.str.upper().str.strip()
            )
        )

    if_process_df_county = if_process_df.merge(
        county_df_fil,
        left_on="route_county",
        right_on="sap_county_id",
        how="left"
    )

    if_process_df_county_agg = (
        if_process_df_county
        .loc[lambda df: df.route_qual==0]
        .groupby(["county_nm", "route_no", "route_class"])
        .agg(
            route_inventory=("route_inventory", "first"),
            route_county=("route_county", "first"),
            route_id=("route_id", "first"),
            ka_cnt=("ka_cnt", sum),
            bc_cnt=("bc_cnt", sum),
            pdo_cnt=("pdo_cnt", sum),
            total_cnt=("total_cnt", sum),
            aadt_2018=("aadt_2018", "mean"),
            seg_len_in_interval=("seg_len_in_interval", sum),
            st_end_diff_aadt=("st_end_diff_aadt", sum),
            inc_fac=("inc_fac", "mean"),
            si_fac=("si_fac", "mean"),
        )
        .reset_index()
        .assign(
            total_cnt_per_year=lambda df: df.total_cnt / 5,
            crash_rate_per_mile_per_year=lambda df: (
                    df.total_cnt / df.seg_len_in_interval / 5
            ),
            inc_fac_county_lev=lambda df:
                    df.crash_rate_per_mile_per_year * df.aadt_2018 / 100000,
        )
    )

    if_process_df_county_agg.loc[:, "si_county_lev"] = get_severity_index(
        if_process_df_county_agg).severity_index


    nathan_inc_fac = pd.read_excel(path_to_nathan_inc_fac)
    pat=re.compile(r"(I|NC|US)-(\d{2,3}).*")
    nathan_inc_fac[["route_class", "route_no"]] = (
        nathan_inc_fac.Freeway.str.extract(pat, expand=True)
    )
    nathan_inc_fac_fil = (
        nathan_inc_fac
        .assign(
            route_class=lambda df: df.route_class.str.strip().replace(
                {"I": "Interstate", "US": "US Route", "NC": "NC Route"}),
            route_no=lambda df: df.route_no.astype(int),
            County=lambda df:df.County.str.upper().str.strip(),
        )
        .rename(columns={
            'Freeway': "route_desc",
            'Division': "division",
            'County': "county",
            'Crashes in 2016': "total_cnt_2016_nath",
            'Centerline Miles': "centerline_mi_nath",
            'Crashes per mile': "crash_rate_per_mile_per_year_nath",
            'County avg AADT': "avg_aadt_nath",
            'NCDOT Incident Factor -- unadjusted': "inc_fac_nath",
            'Severity Index': "si_nath"})
        .filter(items=[
            "route_no", "route_class", "route_desc", "county", "total_cnt_2016_nath",
            "centerline_mi_nath", "crash_rate_per_mile_per_year_nath", "avg_aadt_nath",
            "inc_fac_nath", "si_nath"])
    )

    nathan_inc_fac_fil_qaqc= (
        nathan_inc_fac_fil
        .merge(
            if_process_df_county_agg,
            left_on=["route_no", "route_class", "county"],
            right_on=["route_no", "route_class", "county_nm"],
            how="left"
        )
    )

    fig = make_subplots(rows=3, cols=3)
    plot_pairs = [
        ("inc_fac_nath", "inc_fac", 1, 1),
        ("inc_fac_nath", "inc_fac_county_lev", 1, 2),
        ("total_cnt_2016_nath", "total_cnt_per_year", 1, 3),
        ("centerline_mi_nath", "seg_len_in_interval", 2, 1),
        ("avg_aadt_nath", "aadt_2018", 2, 2),
        ("si_nath", "si_county_lev", 2, 3),
        ("centerline_mi_nath", "st_end_diff_aadt", 3, 1)]

    for pair in plot_pairs:
        trace=px.scatter(
            data_frame=nathan_inc_fac_fil_qaqc,
            x=pair[0],
            y=pair[1],
            hover_data=nathan_inc_fac_fil_qaqc.columns
        )
        fig.add_trace(trace.data[0], row=pair[2], col=pair[3])
        fig.update_xaxes(title_text=pair[0], row=pair[2], col=pair[3])
        fig.update_yaxes(title_text=pair[1], row=pair[2], col=pair[3])
    fig.show()
    plot(
        fig,
        filename=os.path.join(
            path_processed_data,
            f"data_qaqc_nathan.html",
        ),
        auto_open=False,
    )