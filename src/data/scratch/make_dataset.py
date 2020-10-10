import inflection
import geopandas as gpd


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
