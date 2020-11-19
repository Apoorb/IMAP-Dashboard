# -*- coding: utf-8 -*-
import os
import pandas as pd
import geopandas as gpd
from src.utils import get_project_root
from sklearn.preprocessing import minmax_scale

if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_to_raw = os.path.join(path_to_prj_dir, "data", "raw")
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_interim_sratch = os.path.join(path_interim_data, "scratch")
    path_processed_data = os.path.join(path_to_prj_dir, "data", "processed")
    path_to_census = os.path.join(path_to_raw, "CensusTract2010")
    path_to_census_shapefile = os.path.join(path_to_census, "CensusTract2010.shp")
    path_growth_data = os.path.join(path_to_census, "Combined_FlowByCensusTract.csv")
    path_aadt_crash_si = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    crash_aadt_fil_si_geom_gdf = gpd.read_file(path_aadt_crash_si, driver="gpkg")
    route_id_lrs_gdf = crash_aadt_fil_si_geom_gdf.filter(
        items=["route_id", "aadt_interval_left", "aadt_interval_right", "geometry"]
    )
    census_gpd = gpd.read_file(path_to_census_shapefile, driver="shp")
    census_gpd = census_gpd.to_crs(epsg=4326)
    growth_df = pd.read_csv(path_growth_data).assign(
        GEOID10=lambda df: df.GEOID10.astype(str)
    )
    census_gpd_growth = census_gpd.merge(growth_df, on="GEOID10", how="left")
    census_gpd_growth["test_tot_gr_24_yearly"] = (
        (
            (
                census_gpd_growth["2040_Tot_Flow_24h"]
                / census_gpd_growth["2015_Tot_Flow_24h"]
            )
            ** (1 / (2040 - 2015))
        )
        - 1
    ) * 100
    census_gpd_growth["tot_gr_24_yearly"] = (
        ((1 + (census_gpd_growth["24h_Tot_GR"] / 100)) ** (1 / (2040 - 2015))) - 1
    ) * 100
    census_gpd_growth.to_file(
        os.path.join(path_interim_sratch, "census_gpd_growth_polygons.shp")
    )
    census_gpd_growth_lrs = gpd.sjoin(
        route_id_lrs_gdf, census_gpd_growth, how="inner", op="intersects"
    )
    census_gpd_growth_lrs["24h_Tot_GR"].describe()
    census_gpd_growth_lrs["tot_gr_24_yearly"].describe()
    census_gpd_growth_lrs = census_gpd_growth_lrs.sort_values(
        ["route_id", "aadt_interval_left"]
    )
    census_gpd_growth_lrs.tot_gr_24_yearly = (
        census_gpd_growth_lrs.groupby(["route_id"])
        .tot_gr_24_yearly.apply(lambda x: x.ffill().bfill())
    )
    census_gpd_growth_lrs.test_tot_gr_24_yearly = (
        census_gpd_growth_lrs.groupby(["route_id"])
        .test_tot_gr_24_yearly.apply(lambda x: x.ffill().bfill())
    )
    import numpy as np

    mask = ~ census_gpd_growth_lrs.tot_gr_24_yearly.isna()
    assert np.isclose(
        census_gpd_growth_lrs[mask].tot_gr_24_yearly,
        census_gpd_growth_lrs[mask].test_tot_gr_24_yearly,
    ).all()

    census_gpd_growth_lrs_grp = (
        census_gpd_growth_lrs.groupby(
            ["route_id", "aadt_interval_left", "aadt_interval_right"]
        )
        .agg(
            tot_gr_24_yearly=("tot_gr_24_yearly", "mean"),
            GEOID10=("GEOID10", "first"),
            tot_flow_2015_24=("2015_Tot_Flow_24h", "first"),
            tot_flow_2040_24=("2040_Tot_Flow_24h", "first"),
            tot_grw_rt_24=("24h_Tot_GR", "first"),
            geometry=("geometry", "first"),
        )
        .reset_index()
    )
    census_gpd_growth_lrs_grp = gpd.GeoDataFrame(
        census_gpd_growth_lrs_grp, crs=census_gpd_growth_lrs.crs
    )
    len(census_gpd_growth_lrs_grp)
    census_gpd_growth_lrs_grp["growth_fac"] = minmax_scale(
        census_gpd_growth_lrs_grp.tot_gr_24_yearly, (0, 1)
    )

    census_gpd_growth_lrs_grp.to_file(
        os.path.join(path_interim_sratch, "census_gpd_growth.shp")
    )
    census_gpd_growth_lrs_grp.to_file(
        os.path.join(path_processed_data, "census_gpd_growth.gpkg"), driver="GPKG"
    )
