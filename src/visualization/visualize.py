import geopandas as gpd
import os
import seaborn as sns

if __name__ == "__main__":
    path_to_prj_dir = os.getcwd()
    path_interim_data = os.path.join(os.getcwd(), "data", "interim")
    path_crash_si = os.path.join(path_interim_data, "nc_crash_si_2015_2019.gpkg")
    crash_df_fil_si_geom_gdf = gpd.read_file(path_crash_si,
                                             driver="gpkg")
    crash_df_fil_si_geom_gdf.columns