import pandas as pd
import geopandas as gpd
import os
from src.utils import get_project_root
import plotly.io as pio
import json
import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
from shapely.geometry import Point
from folium.features import DivIcon
import seaborn as sns
import numpy as np

pio.renderers.default = "browser"

path_to_prj_dir = get_project_root()
path_to_raw = os.path.join(path_to_prj_dir, "data", "raw")
path_processed_data = os.path.join(path_to_prj_dir, "data", "processed")
path_if_si_detour_nat_imp = os.path.join(
    path_processed_data, "if_si_detour_nat_imp.gpkg"
)
path_to_county = os.path.join(
    path_to_raw, "CountyBoundary_SHP", "BoundaryCountyPolygon.shp",
)
path_to_nathan_inc_fac = os.path.join(path_to_raw, "nathan_inc_fac.xlsx")
path_imap_routes = os.path.join(path_to_raw, "IMAP Routes", "Statewide_IMAP_Routes.shp")
path_to_fig = os.path.join(path_to_prj_dir, "reports", "figures")
path_to_fig_imap = os.path.join(path_to_fig, "imap_folium.html")
########################################################################################################################
# ADD Labels to the line segments
#
# mapobj = my_map
# gdf = dat
# popup_field_list = ["Route_ID","Begin_Poin","End_Point","IF","IF_Adj"]
def add_points_AB_V3(mapobj, gdf, popup_field_list):
    """
    mapobj: folium map object. Will be used for plotting
    gdf: geopandas dataframe having the attributes and line coordinates
    popup_field_list: list of column names which need to displayed on the map
    """
    # Make Data Pretty
    gdf.aadt_interval_left = gdf.aadt_interval_left.round(2)
    gdf.aadt_interval_right = gdf.aadt_interval_right.round(2)
    gdf.inc_fac = gdf.inc_fac.round(1)
    # Need the centroid to create popup pins:
    gdf["geometry"] = gdf.apply(
        lambda z: Point(z.geometry.centroid.x, z.geometry.centroid.y), axis=1
    )
    # Source: https://github.com/python-visualization/folium/pull/376
    # Source IMP:
    # https://github.com/python-visualization/folium/blob/master/examples/MarkerCluster.ipynb
    # Create empty lists to contain the point coordinates and the point pop-up information
    marker_cluster = MarkerCluster(name="IF Popup").add_to(mapobj)

    # https://geoffboeing.com/2015/10/exporting-python-data-geojson/
    # Create GeoJson for Features
    geojson1 = {"type": "FeatureCollection", "features": []}
    # Loop through each record in the GeoDataFrame
    for i, row in gdf.iterrows():
        # Create a string of HTML code used in the IFrame popup
        # Join together the fields in "popup_field_list" with a linebreak between them
        label = "<br>".join(
            [field + ": " + str(row[field]) for field in popup_field_list]
        )
        # Change Popup Width to 150% to get all text inside the box
        # https://python-visualization.github.io/folium/modules.html
        # https://github.com/Leaflet/Leaflet.markercluster
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=folium.Popup(html=label, parse_html=False, max_width="150"),
            icon=folium.Icon(color="green", icon="ok-sign"),
        ).add_to(marker_cluster)

        # https://geoffboeing.com/2015/10/exporting-python-data-geojson/
        feature = {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Point", "coordinates": []},
        }
        feature["geometry"]["coordinates"] = [row.geometry.y, row.geometry.x]
        for prop in popup_field_list:
            feature["properties"][prop] = row[prop]
        geojson1["features"].append(feature)
    # PathMarkers = os.path.join(
    #     os.path.expanduser("~"),
    #     "OneDrive - Kittelson & Associates, Inc",
    #     "Documents",
    #     "IMAP_DashBoard",
    #     "Data",
    #     "FoliumMarkerCluster.json",
    # )
    # with open(PathMarkers, "w", encoding="utf-8") as f:
    #     json.dump(geojson1, f, ensure_ascii=False, indent=4)
    return mapobj


# https://geoffboeing.com/2015/10/exporting-python-data-geojson/


def AddTextCounties(mapobj, gdf, popup_field_list):
    gdf["geometry"] = gdf.apply(
        lambda z: Point(z.geometry.centroid.x, z.geometry.centroid.y), axis=1
    )
    marker_cluster = MarkerCluster(name="County Names").add_to(mapobj)
    # Loop through each record in the GeoDataFrame
    for i, row in gdf.iterrows():
        # Create a string of HTML code used in the IFrame popup
        # Join together the fields in "popup_field_list" with a linebreak between them
        label = "<br>".join([str(row[field]) for field in popup_field_list])
        # Change Popup Width to 150% to get all text inside the box
        # https://python-visualization.github.io/folium/modules.html
        # https://github.com/python-visualization/folium/issues/970
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon=DivIcon(
                html=f"""<div style="font-family: courier new;font size ="18"; color: 'black'">{"{}".format(label)}</div>"""
            ),
        ).add_to(marker_cluster)
    return mapobj


# Plotting data on OSM using foliumm:
# https://ocefpaf.github.io/python4oceanographers/blog/2015/12/14/geopandas_folium/
# Very Helpful:
# https://github.com/python-visualization/folium/blob/master/examples/Colormaps.ipynb
##################################################################
def FoliumMapAB(
    mapobj,
    dat,
    colorFac="IF_Adj",
    ColBins=14,
    caption_="Adjusted Incident Factor",
    name_="IF Heatmap",
    add_color_map=False,
):
    """
    mapobj = folium map object
    dat = Geopandas dataframe used for plotting
    ColBins = # of color bins needed
    """
    # Get dat into GeoPandas DataFrame
    dat = gpd.GeoDataFrame(dat, crs={"init": "epsg:4326"})
    datJson = dat.to_json()  #
    ###############################
    # datJson has "id" node which is the index for the "dat".
    # BUT it is string so convert your
    # index to strings.
    # Create a key value pair for color coding lines:
    dat_dict = dat.set_index(dat.index.astype("str"))[colorFac].sort_index()
    Min1 = 0
    Max1 = 100
    GrYlRe_Pal = ["green"] + sns.color_palette("YlOrRd", ColBins - 1)
    l1 = np.linspace(7, Max1, ColBins).astype("int").tolist()
    l1 = [Min1] + l1
    colormap = cm.StepColormap(
        GrYlRe_Pal, vmin=Min1, vmax=Max1, index=l1, caption=caption_,
    )
    # Add lines on map
    folium.GeoJson(
        datJson,
        name=name_,
        style_function=lambda feature: {
            "fillColor": colormap(dat_dict[feature["id"]]),
            "color": colormap(dat_dict[feature["id"]]),
            "weight": 4,
            "opacity": "0.7"
            # "dashArray": "5, 5",
        },
    ).add_to(mapobj)
    # Add Legend
    if add_color_map:
        colormap.add_to(mapobj)
    return mapobj


if __name__ == "__main__":
    if_process_df = gpd.read_file(path_if_si_detour_nat_imp, driver="gpkg")
    if_process_df.inc_fac = if_process_df.inc_fac.fillna(0)
    if_process_df = if_process_df.rename(
        columns={"crash_rate_per_mile_per_year": "crash_per_mile_per_year"}
    )
    if_process_df["adj_inc_fac"] = (
        if_process_df.inc_fac
        * (1 + if_process_df.si_fac * 0.25)
        * ((1 + if_process_df.detour_fac * 0.25))
    )
    if_process_df.crash_per_mile_per_year = if_process_df.crash_per_mile_per_year.round(
        2
    )
    if_process_df.adj_inc_fac = if_process_df.adj_inc_fac.round(2)
    if_process_df.si_fac = if_process_df.si_fac.round(2)
    if_process_df.detour_fac = if_process_df.detour_fac.round(2)

    county_df = gpd.read_file(path_to_county, driver="shp")
    county_df = county_df.to_crs(epsg=4326)
    imap_gdf = gpd.read_file(path_imap_routes)
    county_df_fil = (
        county_df.filter(items=["FIPS", "CountyName", "SapCountyI", "geometry"])
        .rename(
            columns={
                "FIPS": "fips",
                "CountyName": "county_nm",
                "SapCountyI": "sap_county_id",
            }
        )
        .assign(
            sap_county_id=lambda df: df.sap_county_id.astype(int),
            county_nm=lambda df: df.county_nm.str.upper().str.strip(),
        )
    )

    my_map = folium.Map(location=[34.768897, -78.802428], zoom_start=10)
    folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(my_map)
    my_map = FoliumMapAB(
        my_map, if_process_df, colorFac="adj_inc_fac", add_color_map=True
    )
    # my_map = FoliumMapAB(my_map, if_process_df, colorFac="adj_inc_fac", name_="Adjusted IF Heatmap")
    my_map = add_points_AB_V3(
        my_map,
        if_process_df,
        [
            "route_id",
            "route_class",
            "route_no",
            "route_county",
            "aadt_2018",
            "crash_per_mile_per_year",
            "aadt_interval_left",
            "aadt_interval_right",
            "inc_fac",
            "adj_inc_fac",
            "si_fac",
            "detour_fac",
            "nat_imp_fac",
            "growth_fac",
            "seasonal_fac",
        ],
    )
    folium.GeoJson(
        county_df_fil,
        name="County Boundaries",
        style_function=lambda feature: {"color": "black", "fill": False, "weight": 1},
    ).add_to(my_map)
    # https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/stroke-dasharray
    # http://plnkr.co/edit/KyHOkjytDJf1QjCO0Nyh?p=preview
    # https://leafletjs.com/reference-1.5.0.html#path-dasharray
    my_map = AddTextCounties(my_map, county_df_fil, ["county_nm"])
    imap_json = imap_gdf.to_json()
    folium.GeoJson(
        imap_json,
        name="IMAP Routes",
        style_function=lambda feature: {
            "color": "black",
            "fill": False,
            "weight": 2,
            "dashArray": "6",
        },
    ).add_to(my_map)
    folium.LayerControl(collapsed=True).add_to(my_map)
    my_map.save(path_to_fig_imap)
