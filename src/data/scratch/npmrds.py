# -*- coding: utf-8 -*-
import os
from src.utils import get_project_root
from src.data.make_dataset import read_shp


def filter_npmrds_columns(npmrds_gdf_):
    npmrds_gdf_fil_ = npmrds_gdf_.filter(
        items=[
            "county",
            "zip",
            "tmc_linear",
            "tmc",
            "tmc_type",
            "route_numb",
            "road_name",
            "route_sign",
            "route_qual",
            "alt_rte_name",
            "miles",
            "is_primary",
            "first_name",
            "direction",
            "start_lat",
            "start_long",
            "end_lat",
            "end_long",
            "f_system",
            "urban_code",
            "facil_type",
            "struc_type",
            "thru_lanes",
            "aadt",
            "aadt_singl",
            "aadt_combi",
            "truck",
            "nhs",
            "nhs_pct",
            "strhnt_typ",
            "strhnt_pct",
            "geometry",
        ]
    ).assign(route_numb=lambda df: df.route_numb.astype(int))
    return npmrds_gdf_fil_


def test_missing_values(npmrds_gdf_):
    npmrds_gdf_missing_val_ = npmrds_gdf_[
        npmrds_gdf_[
            [
                "county",
                "tmc_linear",
                "tmc",
                "tmc_type",
                "route_numb",
                "route_qual",
                "direction",
                "geometry",
                "aadt",
            ]
        ]
        .isna()
        .any(axis=1)
    ]
    missing_value = len(npmrds_gdf_missing_val_)
    try:
        assert missing_value == 0, (
            f'Check for {missing_value} missing values in "county", "tmc_linear", "tmc",'
            '"tmc_type", "route_numb", "route_qual", "direction", "geometry", "aadt"'
        )
    except AssertionError as err:
        print(err)
    return npmrds_gdf_missing_val_


if __name__ == "__main__":
    path_to_prj_dir = get_project_root()
    path_to_prj_data = os.path.join(path_to_prj_dir, "data", "raw")
    path_interim_data = os.path.join(path_to_prj_dir, "data", "interim")
    npmrds_file = os.path.join(
        path_to_prj_data, "npmrds-shapefiles", "North Carolina_2019"
    )
    npmrds_gdf = read_shp(npmrds_file)
    npmrds_gdf_missing_val = test_missing_values(npmrds_gdf)
    npmrds_gdf_fil = filter_npmrds_columns(npmrds_gdf)
    npmrds_gdf_fil.route_numb.unique()
    out_file_npmrds_nc = os.path.join(path_interim_data, "npmrds_nc_2019.gpkg")
    npmrds_gdf_fil.to_file(out_file_npmrds_nc, driver="GPKG")
