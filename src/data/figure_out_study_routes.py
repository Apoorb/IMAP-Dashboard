"""
Explore NHS, STC routes. Create shapefiles for visualizing NHS and STC routes.
"""
from io import StringIO
import pandas as pd
import os
from src.utils import get_project_root
import geopandas as gpd


def get_strategic_trans_cor():
    """
    Create a dataframe for North Carolina strategic transportation routes.
    """
    stc_string_io = StringIO(
        """route_class,route_no
        US,74
        US,441
        I,26 
        US,23 
        US,321
        US,421
        I,73
        I,77
        I,74
        I,85
        US,29
        NC,87
        US,1
        I,495
        US,64
        US,13
        US,17 
        US,70
        I,40
        NC,49
        I,795
        US,117
        I,95
        US,264
        US,401
        NC,24
        US,258
        NC,11
        US,158
    """
    )
    stc_df_ = pd.read_csv(stc_string_io)
    stc_df_ = stc_df_.assign(
        route_class=lambda df: df.route_class.astype(str).str.strip(),
        route_no=lambda df: df.route_no.astype(int),
    )
    stc_df_.loc[:, "stc"] = True
    return stc_df_


def test_all_stc_in_study_gdf(
    study_gdf, stc_df_, merge_cols=("route_class", "route_no")
):
    """
    Test all NC strategic transportation routes are in the study df: aadt or crash data.
    Parameters
    ----------
    study_gdf: gpd.GeoDataFrame()
        aadt or crash data.
    stc_df_: pd.DataFrame()
        NC strategic transportation routes.
    merge_cols
        Columns to the merge study_gdf and stc_df_.
    Returns
    -------
    stc_study_routes[~stc_study_routes.route_in_study_gdf]: pd.DataFrame()
        stc DataFrame with routes in stc but not in aadt or crash data.
    """
    study_routes = pd.DataFrame(
        study_gdf[merge_cols]
        .drop_duplicates(subset=merge_cols)
        .reset_index(drop=True)
        .assign(
            route_class=lambda df: df.route_class.replace(
                {1: "I", 2: "US", 3: "NC", 4: "Secondary Routes"}
            ),
            route_in_study_gdf=True,
        )
    )
    stc_study_routes = stc_df_.merge(study_routes, on=merge_cols, how="left").assign(
        route_in_study_gdf=lambda df: df.route_in_study_gdf.fillna(False)
    )
    return stc_study_routes[~stc_study_routes.route_in_study_gdf]


def routes_in_hpms_2018_nhs(hpms_2018_nc_, stc_df_):
    """
    Find routes that both NHS and NC STC routes.
    Parameters
    ----------
    hpms_2018_nc_: pd.DataFrame()
        HPMS 2018 NC data.
    stc_df_: pd.DataFrame()
        North Carolina strategic transportation routes.
    Returns
    -------
    hpms_2018_nc_fil_stc: pd.DataFrame()
        Dataframe with a columns "stc" that is true if an NHS route is also a STC route.
    """
    hpms_2018_nc_fil_ = (
        hpms_2018_nc_.query("nhs != 0")
        .replace({"route_sign": {2: "I", 3: "US", 4: "NC"}})
        .query("route_sign in ['I', 'US', 'NC']")
        .assign(nhs_net=True)
        .filter(
            items=[
                "route_sign",
                "route_numb",
                "route_qual",
                "nhs",
                "nhs_net",
                "strahnet_t",
            ]
        )
        .drop_duplicates(["route_sign", "route_numb"])
    )

    hpms_2018_nc_fil_stc = (
        hpms_2018_nc_fil_.merge(
            stc_df_,
            left_on=["route_sign", "route_numb"],
            right_on=["route_class", "route_no"],
            how="outer",
        )
        .assign(stc=lambda df: df.stc.fillna(False))
        .sort_values(["route_numb", "route_numb"])
    )
    return hpms_2018_nc_fil_stc


if __name__ == "__main__":
    # Set the paths to relevant files and folders.
    # Load cleaned AADT, crash, AADT+Crash data; output form crash.py, aadt.py, and
    # aadt_crash_merge.py.
    # Load HPMS NC 2018 raw data to get NHS information for the routes.
    # ************************************************************************************
    path_to_prj_dir = get_project_root()
    path_to_prj_data = os.path.join(path_to_prj_dir, "data", "raw")
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_crash_si = os.path.join(path_interim_data, "nc_crash_si_2015_2019.gpkg")
    path_aadt_nc = os.path.join(path_interim_data, "ncdot_2018_aadt.gpkg")
    path_aadt_crash = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    path_hpms_2018 = os.path.join(
        path_to_prj_data, "hpms_northcarolina2018", "NorthCarolina_PR_2018.shp"
    )
    hpms_2018_nc = gpd.read_file(path_hpms_2018)
    crash_df_fil_si_geom_gdf = gpd.read_file(path_crash_si, driver="gpkg")
    aadt_df = gpd.read_file(path_aadt_nc, driver="gpkg")
    stc_df = get_strategic_trans_cor().assign(stc=True)
    aadt_crash_gdf = gpd.read_file(path_aadt_crash, driver="gpkg")

    # Test for missing stc routes in aadt or crash data.
    # ************************************************************************************
    test_all_stc_in_study_gdf(crash_df_fil_si_geom_gdf, stc_df)
    test_all_stc_in_study_gdf(aadt_df, stc_df)

    # Find routes in hpms nhs and not in stc
    # ************************************************************************************
    hpms_2018_nc_fil = routes_in_hpms_2018_nhs(
        hpms_2018_nc_=hpms_2018_nc, stc_df_=stc_df
    )
    # Output routes in hpms nhs and not in stc
    # ************************************************************************************
    out_path_hpms_2018_nc_fil = os.path.join(
        path_interim_data, "nhs_hpms_2018_routes.csv"
    )
    hpms_2018_nc_fil.to_csv(out_path_hpms_2018_nc_fil, index=False)

    # Routes not in AADT data
    # ************************************************************************************
    print(
        f"{set(hpms_2018_nc_fil.route_numb) - set(aadt_df.route_no)} "
        f"routes not in aadt data"
    )

    # Find routes in hpms nhs and not in stc. Keep all NHS line segments.
    # Don't drop duplicates. Will plot in GIS.
    # ************************************************************************************
    hpms_2018_nc_fil_all = (
        hpms_2018_nc.query("nhs != 0")
        .replace({"route_sign": {2: "I", 3: "US", 4: "NC"}})
        .query("route_sign in ['I', 'US', 'NC']")
        .assign(nhs_net=True)
    )
    hpms_2018_nc_fil_all = hpms_2018_nc_fil_all.merge(
        stc_df, left_on=["route_numb"], right_on=["route_no"], how="outer",
    ).assign(stc=lambda df: df.stc.fillna(False))

    out_file_hpms_stc = os.path.join(
        path_interim_data, "hpms_2018_nhs_stc_gis_visual_check.gpkg"
    )
    hpms_2018_nc_fil_all.to_file(out_file_hpms_stc, driver="GPKG")

    # Find routes in aadt_crash_gdf that are in HPMS NHS.
    # ************************************************************************************
    # Drop route_class for merge for now
    hpms_2018_routes = set(hpms_2018_nc_fil.route_numb)
    aadt_crash_gdf_nhs = aadt_crash_gdf.query("route_no in @hpms_2018_routes")
    out_file_aadt_crash_nhs = os.path.join(
        path_interim_data, "", "aadt_crash_nhs_gis_visual_check_v1.shp"
    )
    aadt_crash_gdf_nhs.to_file(out_file_aadt_crash_nhs)
