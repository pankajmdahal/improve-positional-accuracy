
clip_distance = "10 Miles"

buffer_dist = 1.7  # default buffer distance (to find new nodes close to old nodes)
near_snap_dist = "2 Mile"  # the distance to which the old nodes has to snapped to the new network
network_buffer_dist = 5

old_nodes_shp = 'intermediate/shp/nodes_old.shp'
old_links_shp = '../shp/Rail2M_/Rail2MLinks.shp'

new_links_shp = '../shp/railway_ln_connected/railway_ln_connected.shp'
new_nodes_shp = 'intermediate/shp/nodes_new.shp'

new_links_clipped = 'intermediate/shp/new_links_clipped.shp'


snapped_old_nodes = 'C:/GIS/snapped.shp'
old_links_cropped_shp = 'intermediate/shp/cropped_old_network.shp'
temp1f = "temp1f"


# temporary files
o = "in_memory/o"  # temporary files
d = "in_memory/d"
m = "in_memory/m"

feature = "C:/GIS/feature.shp" # i guess this is just a temporary layer/ no worries
temp = "C:/GIS/temp.shp"
temp1 = "C:/GIS/temp1.shp"
temp2 = "C:/GIS/temp2.shp"


B1_ND = "intermediate/shp/B1_ND.nd"
B1_route = "B1_route"

#csv files
old_new_csv = "old_new_dict.csv"
route_not_found_csv = "route_not_found.csv"
min_max_csv = "min_max.csv"
multiple_minimum_csv = "multiple_minimum.csv"



#links
sumlayer_l = "C:/GIS/sumlayer_l.shp"
sumlayer_n = "C:/GIS/sumlayer_n.shp"

emptyshapefile = "C:/GIS/empty.shp"
new_new_nodes = "intermediate/shp/_new_nodes.shp"
