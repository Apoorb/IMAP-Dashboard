# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from src.utils import get_project_root
import inflection
import re
from sklearn.preprocessing import minmax_scale

if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_to_raw = os.path.join(path_to_prj_dir, "data", "raw")
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_interim_sratch = os.path.join(path_interim_data, "scratch")
    path_to_padt = os.path.join(path_to_raw, "SEG_T3_All Routes_Revised")
    path_to_padt_shapefile = os.path.join(
        path_to_padt, "SEG_T3_PADT_All_Routes_Revised.shp"
    )
    path_processed_data = os.path.join(path_to_prj_dir, "data", "processed")
    path_aadt_crash_si = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    crash_aadt_fil_si_geom_gdf = gpd.read_file(path_aadt_crash_si, driver="gpkg")
    route_id_lrs_gdf = crash_aadt_fil_si_geom_gdf.filter(
        items=[
            "route_id",
            "aadt_interval_left",
            "aadt_interval_right",
            "route_class",
            "route_qual",
            "route_inventory",
            "route_county",
            "route_no",
            "geometry",
        ]
    ).assign(
        business_route=lambda df: df.route_qual.apply(
            lambda series: "business" if series == 9 else np.nan
        )
    )

    padt_gpd = gpd.read_file(path_to_padt_shapefile, driver="shp")
    padt_gpd = padt_gpd.to_crs(epsg=4326)
    padt_gpd.columns = [inflection.underscore(col) for col in padt_gpd.columns]
    padt_gpd = padt_gpd[
        ["rte_1_nbr", "rte_1_clss", "street_nam", "padt_rec", "geometry"]
    ]
    pat_bus = re.compile(r"\S+\s+(\S.*)$", flags=re.IGNORECASE)
    padt_gpd["route_qual_padt"] = padt_gpd.street_nam.str.extract(pat_bus)
    padt_gpd["route_qual_padt"] = padt_gpd.route_qual_padt.str.strip().str.lower()
    padt_gpd.rte_1_clss = padt_gpd.rte_1_clss.str.strip().str.upper()
    padt_gpd["route_class"] = np.select(
        [
            padt_gpd.rte_1_clss == "I",
            padt_gpd.rte_1_clss == "US",
            padt_gpd.rte_1_clss == "NC",
        ],
        [1, 2, 3],
        np.nan,
    )
    padt_gpd["route_qual_padt"] = np.select(
        [
            padt_gpd["route_qual_padt"] == np.nan,
            padt_gpd["route_qual_padt"] == "alternate",
            padt_gpd["route_qual_padt"] == "bypass",
            padt_gpd["route_qual_padt"] == "east",
            (padt_gpd["route_qual_padt"] == "connector")
            | (padt_gpd["route_qual_padt"] == "spur"),
            padt_gpd["route_qual_padt"] == "truck route",
            (padt_gpd["route_qual_padt"] == "business")
            | (padt_gpd["route_qual_padt"] == "bus"),
        ],
        [0, 1, 2, 5, 7, 8, 9],
    )
    padt_gpd = padt_gpd.query("~ route_class.isna()")
    padt_gpd.rte_1_nbr = padt_gpd.rte_1_nbr.astype(int)

    route_id_lrs_grp = route_id_lrs_gdf.groupby(["route_class", "route_no"])
    padt_gpd_grp = padt_gpd.groupby(["route_class", "rte_1_nbr"])
    route_cls_no_not_found = []
    inc_fac_padt_gpd = gpd.GeoDataFrame()
    inc_fac_padt_gpd_list = []
    for name, route_id_lrs_sub_grp in route_id_lrs_grp:
        if name not in padt_gpd_grp.groups.keys():
            route_cls_no_not_found.append(name)
            continue
        padt_sub_gpd = padt_gpd_grp.get_group(name)
        inc_fac_padt_gpd_list.append(
            gpd.sjoin(left_df=route_id_lrs_sub_grp, right_df=padt_sub_gpd, how="left",)
        )

    inc_fac_padt_gpd = pd.concat(inc_fac_padt_gpd_list, ignore_index=True)
    inc_fac_padt_gpd = (
        inc_fac_padt_gpd.groupby(
            ["route_id", "aadt_interval_left", "aadt_interval_right"]
        )
        .agg(padt_rec=("padt_rec", "max"), geometry=("geometry", "first"),)
        .reset_index()
    )
    inc_fac_padt_gpd = gpd.GeoDataFrame(inc_fac_padt_gpd, crs=route_id_lrs_gdf.crs)
    inc_fac_padt_gpd["seasonal_fac"] = minmax_scale(inc_fac_padt_gpd.padt_rec, (0, 1))
    inc_fac_padt_gpd.to_file(
        os.path.join(path_processed_data, "padt_on_inc_fac_gis.gpkg"), driver="GPKG"
    )
