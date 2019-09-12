#parameters
buffer_dist = 50.0 #feet
threshold = 50.0
clip_state_list = ["'TN'"]
# keep on going to 200 feet if not found
buffer_dist_list = ['20 feet','40 feet','60 feet','80 feet','100 feet','120 feet', '140 feet','160 feet','180 feet','200 feet']


#temporary files
m = "in_memory/T4"
m1 = "in_memory/m1"
p1 = "in_memory/p1"
temp = "C:/GIS/temp.shp"
temp_shp1 = "in_memory/T1"

#folders
intermediate_folder = './intermediate/'
shp_folder = './input/'


# output shp to GIS
output_no_routes_shp = "C:/GIS/noroutes.shp"
output_tolerance_exceed_shp = "C:/GIS/exceedtolerance.shp"
output_buffer_tolerance_exceed_shp = "C:/GIS/exceedbuffertolerance.shp"

# shape files
feature = "feature"
#f = "C:/GIS/temp.shp"
f = "in_memory/T2"
base_f = "base_f"
other_f = "other_f"
other_pt_f = "other_pt"
buffer_shp = "in_memory/b1"
route_shp = "route_shp"
clip_area_shp = "../shp/clip_area/TN.shp"

#intermediate shp files
all_area_shp = "../shp/clip_area/all.shp"
all_area_shp_f = "allarea"
clip_area_shp = "../shp/clip_area/clip.shp"
temp_shp1 = "C:/GIS/T1.shp"
clipped_dataset = "./intermediate/clipped_dataset.shp"
clipped_dataset_f = "./intermediate/clipped_dataset_f.shp"
clipped_dataset_pt = "./intermediate/pt_clipped_dataset.shp"

#network datasets
network_dataset = "./intermediate/network_dataset.shp"
network_dataset_ND = "./intermediate/network_dataset_ND.nd"
all_dataset = "./intermediate/railway_ln_connected.shp"
all_dataset_ND = "./intermediate/railway_ln_connected_ND.nd"

# csv files
no_routes = "noroutes.csv"
no_tolerance = "notolerance.csv"
no_tolerance_buffer = "notolerancebuffer.csv"
node_coordinates_dict = "node_near_coordinates_dict.csv"
no_nearby_dict = "no_nearby.csv"
id_buffer_dict = "id_buffer_dict.csv"