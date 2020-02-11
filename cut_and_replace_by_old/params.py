import numpy as np
import arcpy

arcpy.env.overwriteOutput = True

search_dist_list = np.linspace(0.2, 4, 20)# miles distance to where the new links has to be found (1 used but one feature is over 1 mile)

buffer_dist = 100 #ft distance where the links like
search_dist = 2 #miles distance to where the new links has to be found
snap_dist = 5280 #ft (validated distance)

#csv
abbr_to_fips = "abbr_to_fips.csv"
fips_rr_input = "../../RAIL11/RAIL/input/FIPSRR.csv"
fips_rr_output = "../../RAIL/input/FIPSRR.csv"

new_shp = '../../RAIL11/RAIL/gis/alllinks.shp'
old_shp = '../../RAIL11/RAIL/gis/old_links.shp'
final_output = '../../RAIL/gis/alllinks.shp'
all_states = 'input/shp/tl_2017_us_states.shp'


clip_state_list = ["'TN'", "'NC'","'SC'","'GA'","'FL'","'AL'","'MS'"]
colname_list = ['FID', 'ID', 'RR1', 'RR2', 'RR3', 'RR4', 'RR5', 'LINK_TYPE', 'SIGNAL', 'CAPY_CODE', 'FF_SPEED']