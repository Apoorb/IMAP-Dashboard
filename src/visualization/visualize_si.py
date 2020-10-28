"""
Visualize severity index using pdf, cdf, and k-means clustering.
Created by: Apoorba Bibeka
"""
import pandas as pd
import geopandas as gpd
import os
import seaborn as sns
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
from src.utils import get_project_root


plt.rcParams.update({'font.size': 14})

sns.set_style("whitegrid")
LOC_Y = plticker.MultipleLocator(
        base=0.1
    )  # this locator puts ticks at regular intervals
LOC_X = plticker.MultipleLocator(
        base=4
    )  # this locator puts ticks at regular intervals


def plot_cdf_pdf(crash_df_fil_si_geom_gdf_no_nan_,
                 quantile_90th_,
                 loc_x=LOC_X,
                 loc_y=LOC_Y,
                 y_var="severity_index",
                 y_label="Severity Index",
                 title_="2015-2019 Severity Index CDF",
                 img_file_="severity_index_cdf_2015_2019"):
    """

    Parameters
    ----------
    crash_df_fil_si_geom_gdf_no_nan_
    quantile_90th_
    loc_x
    loc_y
    title_
    img_file_

    Returns
    -------

    """
    si_cdf_plot = sns.distplot(
        crash_df_fil_si_geom_gdf_no_nan_[y_var], hist_kws={"cumulative": True},
        kde_kws={"cumulative": True},
    )
    sns.distplot(
        crash_df_fil_si_geom_gdf_no_nan_[y_var],
        ax=si_cdf_plot,
        axlabel=y_label,
    )
    si_cdf_plot.set_title(title_)
    if bool(loc_x):
        si_cdf_plot.xaxis.set_major_locator(loc_x)
    if bool(loc_y):
        si_cdf_plot.yaxis.set_major_locator(loc_y)
    plt.axvline(quantile_90th_, color='red')
    plt.text(quantile_90th_-10, 0.90, r"$90^{th}$"+"\nPercentile\n= "f"{round(quantile_90th_,2)}", fontsize=10)
    si_cdf_plot_fig = si_cdf_plot.get_figure()
    plt.tight_layout()
    si_cdf_plot_fig.set_size_inches(6, 4)
    si_cdf_plot_fig.savefig(
        fname=os.path.join(path_to_fig, f"{img_file_}.png")
    )
    plt.close()
    return 0


def plot_facet_cdf_pdf(crash_df_fil_si_geom_gdf_no_nan_,
                       loc_x=LOC_X,
                       loc_y=LOC_Y,
                       y_var="severity_index",
                       y_label="Severity Index",
                       title_="2015-2019 Severity Index CDF for Different Route Class",
                       img_file_="severity_index_cdf_2015_2019_rt_cls",
                       facet_col_="route_class",
                       sharex_=True):
    """

    Parameters
    ----------
    crash_df_fil_si_geom_gdf_no_nan_
    loc_x
    loc_y
    title_
    img_file_
    facet_col_
    sharex_

    Returns
    -------

    """
    si_cdf_plot_rt_cls = sns.FacetGrid(
        crash_df_fil_si_geom_gdf_no_nan_, col=facet_col_, height=4, aspect=1,
        sharex=sharex_
    )
    si_cdf_plot_rt_cls.map(
        sns.distplot, y_var, hist_kws={"cumulative": True},
        kde_kws={"cumulative": True}
    )
    si_cdf_plot_rt_cls.map(sns.distplot, y_var, color="orange")
    for ax in si_cdf_plot_rt_cls.axes.flat:
        if bool(loc_x):
            ax.xaxis.set_major_locator(loc_x)
        if bool(loc_y):
            ax.yaxis.set_major_locator(loc_y)
    plt.subplots_adjust(top=0.85)
    si_cdf_plot_rt_cls.fig.suptitle(title_)
    si_cdf_plot_rt_cls.set_xlabels(y_label)
    plt.tight_layout()
    si_cdf_plot_rt_cls.savefig(
        fname=os.path.join(path_to_fig, f"{img_file_}.png")
    )
    plt.close()
    return 0


def apply_kmeans_cluster_plot(crash_df_fil_si_geom_gdf_no_nan_):
    """

    Parameters
    ----------
    crash_df_fil_si_geom_gdf_no_nan_

    Returns
    -------

    """
    X = crash_df_fil_si_geom_gdf_no_nan_.severity_index.values.reshape(-1, 1)
    kmeans_si = KMeans(n_clusters=2, random_state=0).fit(X)
    list(kmeans_si.labels_)
    colors = ["r", "b"]
    centroids = kmeans_si.cluster_centers_
    Z = kmeans_si.predict(X)
    fig_kmean_si_center, ax_kmean_si_center = plt.subplots()
    loc_y_centroid = plticker.MultipleLocator(
        base=2
    )  # this locator puts ticks at regular intervals
    for n, y in enumerate(centroids):
        ax_kmean_si_center.plot(1, y, marker="x", color=colors[n], ms=10)
        ax_kmean_si_center.yaxis.set_major_locator(loc_y_centroid)
    ax_kmean_si_center.set_title("Severity Index Kmeans Cluster Centroids")
    fig_kmean_si_center.savefig(
        fname=os.path.join(path_to_fig, "severity_index_kmeans_centroids.png")
    )

    # Plot each class as a separate colour
    n_clusters = 2
    fig_kmean_si, ax_kmean_si = plt.subplots()
    for n in range(n_clusters):
        # Filter data points to plot each in turn.
        ys = crash_aadt_fil_si_geom_gdf_no_nan.severity_index.values[Z == n]
        xs = crash_aadt_fil_si_geom_gdf_no_nan.severity_index.index[Z == n]
        ax_kmean_si.scatter(xs, ys, color=colors[n])
        ax_kmean_si.yaxis.set_major_locator(loc_y_centroid)
    ax_kmean_si.set_title("Severity Index Points by Cluster")
    fig_kmean_si.savefig(
        fname=os.path.join(path_to_fig, "severity_index_points_kmeans_cluster.png")
    )
    return 0


if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    path_processed_data = os.path.join(path_to_prj_dir, "data", "processed")
    path_crash_aadt_si = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    path_to_fig = os.path.join(path_to_prj_dir, "reports", "figures")
    path_hpms_2018_nc_fil = os.path.join(
        path_interim_data, "nhs_hpms_2018_routes.csv"
    )
    hpms_2018_nc_fil = pd.read_csv(path_hpms_2018_nc_fil)
    crash_aadt_fil_si_geom_gdf = gpd.read_file(path_crash_aadt_si, driver="gpkg")

    crash_aadt_fil_si_geom_gdf = (
        crash_aadt_fil_si_geom_gdf
        .assign(
            route_class=lambda df: df.route_class.replace(
                {1: "Interstate", 2: "US Route", 3: "NC Route", 4: "Secondary Routes"},
            )
        )
        .query("route_class in ['Interstate', 'US Route', 'NC Route']")
        )
    crash_aadt_fil_si_geom_gdf_no_nan = crash_aadt_fil_si_geom_gdf.query(
        "~ severity_index.isna()"
    )
    crash_aadt_fil_si_geom_gdf.groupby("route_class").severity_index.quantile(.95)
    crash_aadt_fil_si_geom_gdf_no_nan.severity_index.describe()
    quantile_90th_si = crash_aadt_fil_si_geom_gdf.severity_index.quantile(.90)
    plot_cdf_pdf(crash_aadt_fil_si_geom_gdf_no_nan,
                 quantile_90th_=quantile_90th_si)

    plt.rcParams.update({'font.size': 14,
                         'xtick.labelsize':10})
    plot_facet_cdf_pdf(crash_aadt_fil_si_geom_gdf_no_nan)
    plot_facet_cdf_pdf(
        crash_df_fil_si_geom_gdf_no_nan_=crash_aadt_fil_si_geom_gdf_no_nan,
        loc_x=LOC_X,
        loc_y=LOC_Y,
        y_var="severity_index",
        y_label="Severity Index",
        title_="2015-2019 Severity Index CDF for Different Route Class",
        img_file_="severity_index_cdf_2015_2019_rt_cls_vary_scale",
        facet_col_="route_class",
        sharex_=False)

    quantile_90th_inc_fac = crash_aadt_fil_si_geom_gdf.inc_fac.quantile(.90)
    crash_aadt_fil_si_geom_gdf.inc_fac.describe()
    plot_cdf_pdf(crash_df_fil_si_geom_gdf_no_nan_=crash_aadt_fil_si_geom_gdf_no_nan,
                 quantile_90th_=quantile_90th_inc_fac,
                 loc_x=None,
                 loc_y=LOC_Y,
                 y_var="inc_fac",
                 y_label="Incident Factor",
                 title_="Incident Factor",
                 img_file_="inc_fac_cdf")

    plot_facet_cdf_pdf(
        crash_df_fil_si_geom_gdf_no_nan_=crash_aadt_fil_si_geom_gdf_no_nan,
        loc_x=None,
        loc_y=LOC_Y,
        y_var="inc_fac",
        y_label="Incident Factor",
        title_="Incident Factor CDF for Different Route Class",
        img_file_="inc_fac_cdf_rt_cls",
        facet_col_="route_class",
        sharex_=True
    )

    apply_kmeans_cluster_plot(crash_aadt_fil_si_geom_gdf_no_nan)
    set(hpms_2018_nc_fil.route_numb) - set(crash_aadt_fil_si_geom_gdf.route_no.unique())
