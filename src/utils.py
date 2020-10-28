from pathlib import Path
import inflection
import geopandas as gpd


def get_project_root() -> Path:
    return Path(__file__).parent.parent

def reorder_columns(df, first_cols):
    new_col_order = first_cols + [col for col in df.columns if col not in first_cols]
    df = df.reindex(columns = new_col_order)
    return  df


def read_shp(file, data_name=""):
    """
    Parameters
    ----------
    data_name
    crash_file_

    Returns
    -------

    """
    gdf_ = gpd.read_file(file)
    print(f"{data_name} cooridnate sytem is {gdf_.crs.srs}")
    gdf_.columns = [inflection.underscore(col_name) for col_name in gdf_.columns]
    return gdf_
