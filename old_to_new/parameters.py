# what portion of the new network has to be considered? This would significantly reduce the size of network dataset and consequently reduce execution time
clip_distance = "10 Miles"


near_snap_dist = "2 Mile"  # the distance to which the old nodes has to snapped to the new network
network_buffer_dist = 5

extent_switch = 1 #set this to one if the new network is significantly bigger

#generic shapefiles :)
old_links_shp = "../../RAIL11/RAIL/gis/old_links.shp"
new_links_shp = './shp/railway_ln_connected.shp'


#all of these are temporary
new_nodes_shp = './shp/intermediate/nodes_new.shp'
new_links_clipped = './shp/intermediate/new_links_clipped.shp'
snapped_old_nodes = 'C:/GIS/snapped.shp'
old_links_cropped_shp = './shp/intermediate/cropped_old_network.shp'
temp1f = "temp1f"

# temporary/intermediate files
o = "in_memory/o"  # temporary files
d = "in_memory/d"
m = "in_memory/m"

feature = "C:/GIS/feature.shp"  # i guess this is just a temporary layer/ no worries
temp = "C:/GIS/temp.shp"
temp1 = "C:/GIS/temp1.shp"
temp2 = "C:/GIS/temp2.shp"
temp3 = "C:/GIS/temp3.shp"

#for validation
correct_nodes_shp = './shp/allnodes.shp'



emptyshapefile = "C:/GIS/empty.shp"
new_new_nodes = "./shp/intermediate/_new_nodes.shp"
old_nodes_shp = './shp/intermediate/nodes_old.shp'

# network dataset files
B1_ND = "./shp/intermediate/B1_ND.nd"
B1_route = "B1_route"

# csv files
old_new_csv = "./csv/old_new_dict.csv"
route_not_found_csv = "./csv/route_not_found.csv"
min_max_csv = "./csv/min_max.csv"
multiple_minimum_csv = "./csv/multiple_minimum.csv"
