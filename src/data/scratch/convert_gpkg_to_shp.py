import os
from src.utils import get_project_root
import geopandas as gpd

if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_to_prj_data = os.path.join(path_to_prj_dir, "data", "raw")
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_interim_sratch = os.path.join(path_interim_data, "scratch")
    if not os.path.exists(path_interim_sratch):
        os.mkdir(path_interim_sratch)
    path_crash_si = os.path.join(path_interim_data, "nc_crash_si_2015_2019.gpkg")
    path_aadt_nc = os.path.join(path_interim_data, "ncdot_2018_aadt.gpkg")
    path_aadt_crash = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    aadt_df = gpd.read_file(path_aadt_nc, driver="gpkg")
    crash_df_fil_si_geom_gdf = gpd.read_file(path_crash_si, driver="gpkg")
    aadt_crash_gdf = gpd.read_file(path_aadt_crash, driver="gpkg")
    aadt_df.to_file(os.path.join(path_interim_sratch, "ncdot_2018_aadt.shp"))
    crash_df_fil_si_geom_gdf.to_file(
        os.path.join(path_interim_sratch, "nc_crash_si_2015_2019.shp")
    )
    aadt_crash_gdf.to_file(os.path.join(path_interim_sratch, "aadt_crash_ncdot.shp"))
