
## List of Files and Folders

1. if_si_calc.py Use the *aadt_crash_ncdot.gpkg* to compute severity index (SI) and 
   incidence factor (IF). Output IF and SI to *inc_fac_si_scaled.gpkg* in processed
   data folder.
   
2. if_si_detour_nat_imp_census_padt_merge.py: Merge, clean, and filter 
   *inc_fac_si_scaled.gpkg*, *detour_work_ASG.shp*, *padt_on_inc_fac_gis.gpkg*, 
   *census_gpd_growth.gpkg* to output *if_si_detour_nat_imp_census_padt.gpkg*.
   
3. get_if_by_county_qaqc.py: QAQC IF and SI based on Nathan's county level data.
