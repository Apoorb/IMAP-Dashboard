import geopandas as gpd
import os
import seaborn as sns
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
from src.utils import get_project_root

sns.set_style("whitegrid")
LOC_Y = plticker.MultipleLocator(
        base=0.1
    )  # this locator puts ticks at regular intervals
LOC_X = plticker.MultipleLocator(
        base=4
    )  # this locator puts ticks at regular intervals


def plot_cdf_pdf(crash_df_fil_si_geom_gdf_no_nan_,
                 loc_x=LOC_X,
                 loc_y=LOC_Y,
                 title_="2015-2019 Severity Index CDF",
                 img_file_="severity_index_cdf_2015_2019"):
    si_cdf_plot = sns.distplot(
        crash_df_fil_si_geom_gdf_no_nan_.severity_index, hist_kws={"cumulative": True},
        kde_kws={"cumulative": True},
    )
    sns.distplot(
        crash_df_fil_si_geom_gdf_no_nan_.severity_index,
        ax=si_cdf_plot,
        axlabel="Severity Index",
    )
    si_cdf_plot.set_title(title_)
    if bool(loc_x):
        si_cdf_plot.xaxis.set_major_locator(loc_x)
    if bool(loc_y):
        si_cdf_plot.yaxis.set_major_locator(loc_y)
    si_cdf_plot_fig = si_cdf_plot.get_figure()
    si_cdf_plot_fig.savefig(
        fname=os.path.join(path_to_fig, f"{img_file_}.png")
    )
    return 0


def plot_facet_cdf_pdf(crash_df_fil_si_geom_gdf_no_nan_,
                       loc_x=LOC_X,
                       loc_y=LOC_Y,
                       title_="2015-2019 Severity Index CDF for Different Route Class",
                       img_file_="severity_index_cdf_2015_2019_rt_cls",
                       facet_col_="route_class",
                       sharex_=True):
    si_cdf_plot_rt_cls = sns.FacetGrid(
        crash_df_fil_si_geom_gdf_no_nan_, col=facet_col_, height=4, aspect=1,
        sharex=sharex_
    )
    si_cdf_plot_rt_cls.map(
        sns.distplot, "severity_index", hist_kws={"cumulative": True},
        kde_kws={"cumulative": True}
    )
    si_cdf_plot_rt_cls.map(sns.distplot, "severity_index", color="orange")
    for ax in si_cdf_plot_rt_cls.axes.flat:
        if bool(loc_x):
            ax.xaxis.set_major_locator(loc_x)
        if bool(loc_y):
            ax.yaxis.set_major_locator(loc_y)
    plt.subplots_adjust(top=0.85)
    si_cdf_plot_rt_cls.fig.suptitle(title_)
    si_cdf_plot_rt_cls.set_xlabels("Severity Index")
    si_cdf_plot_rt_cls.savefig(
        fname=os.path.join(path_to_fig, f"{img_file_}.png")
    )
    return 0


def apply_kmeans_cluster_plot(crash_df_fil_si_geom_gdf_no_nan_):
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
        ys = crash_df_fil_si_geom_gdf_no_nan.severity_index.values[Z == n]
        xs = crash_df_fil_si_geom_gdf_no_nan.severity_index.index[Z == n]
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
    path_crash_si = os.path.join(path_interim_data, "aadt_crash_ncdot.gpkg")
    path_to_fig = os.path.join(path_to_prj_dir, "reports", "figures")

    crash_df_fil_si_geom_gdf = gpd.read_file(path_crash_si, driver="gpkg")
    crash_df_fil_si_geom_gdf = crash_df_fil_si_geom_gdf.assign(
        route_class=lambda df: df.route_class.replace(
            {1: "Interstate", 2: "US Route", 3: "NC Route"}
        )
    )
    crash_df_fil_si_geom_gdf_no_nan = crash_df_fil_si_geom_gdf.query(
        "~ severity_index.isna()"
    )
    plot_cdf_pdf(crash_df_fil_si_geom_gdf_no_nan)
    plot_facet_cdf_pdf(crash_df_fil_si_geom_gdf_no_nan)
    plot_facet_cdf_pdf(
        crash_df_fil_si_geom_gdf_no_nan_=crash_df_fil_si_geom_gdf_no_nan,
        loc_x=LOC_X,
        loc_y=LOC_Y,
        title_="2015-2019 Severity Index CDF for Different Route Class",
        img_file_="severity_index_cdf_2015_2019_rt_cls_vary_scale",
        facet_col_="route_class",
        sharex_=False)

    apply_kmeans_cluster_plot(crash_df_fil_si_geom_gdf_no_nan)
    set(crash_df_fil_si_geom_gdf_no_nan.route_no.unique())