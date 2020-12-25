
## List of Files and Folders

1. aadt.py: Process the *NCDOT 2018 AADT Traffic Segment* data to fix data types, filter
   to I, US, and NC routes, and add columns to the AADT data. Also, re-project 
   the data to ESG: 4326. This script outputs *ncdot_2018_aadt.gpkg* to the interim data 
   folder.

2. crash.py: Process the *2015 – 2019 Section Safety Scores* data to fix data types, 
   filter to I, US, and NC routes, and add columns to the crash data. Also, re-project 
   the data to ESG: 4326. This script outputs *nc_crash_si_2015_2019.gpkg* to the interim 
   data folder.

3. aadt_crash_merge.py: Merge AADT and Crash data for all Interstates, US Routes, and NC 
   Routes in North Carolina. Specifically, merge *ncdot_2018_aadt.gpkg* and 
   *nc_crash_si_2015_2019.gpkg* using the linear referencing system. This file outputs
   *aadt_crash_ncdot.gpkg* to the interim folder.

4. get_info_on_nhs_stc.py: Use Strategic Transportation Corridors (STC) ppt and the
   HPMS 2018 shapefile to find routes of strategic importance for NC and at national 
   level. This file output *nhs_hpms_stc_routes.csv* to the interim folder.

5. padt.py: Use *SEG_T3_PADT_All_Routes_Revised.shp* to get the PADT. Iterate over the 
    *aadt_crash_ncdot.gpkg* routes and spatial join the PADT data to the AADT+Crash data.
   This file outputs *padt_on_inc_fac_gis.gpkg* to the processed data folder.
   
6. census_growth_rate.py: Use the *CensusTract2010.shp* and the 
   *Combined_FlowByCensusTract.csv* to get the annual growth rate for 24 hours. Spatial 
   join to the *aadt_crash_ncdot.gpkg* file to get the growth rates on the same LRS as the
   AADT+Crash data. Output *census_gpd_growth.gpkg* to the processed data folder.
