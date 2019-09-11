# finding routes that are not

import arcpy
import pandas
import os

arcpy.env.overwriteOutput = True

# parameters
buffer_dist = 50 #feet
threshold = 50  # %
a_list = []
b_list = []
clip_state_list = ["'TN'"]
# clip_state_list = []


# shape files
m = "in_memory/T4"
m = "C:/GIS/temp.shp"
feature = "feature"
f = "C:/GIS/temp.shp"
base_f = "base_f"
other_f = "other_f"
buffer_shp = "in_memory/b1"
route_shp = "route_shp"

# output shp
output_no_routes_shp = "C:/GIS/noroutes.shp"
output_tolerance_exceed_shp = "C:/GIS/exceedtolerance.shp"
output_buffer_tolerance_exceed_shp = "C:/GIS/exceedbuffertolerance.shp"


all_area_shp = "../shp/clip_area/all.shp"
all_area_shp_f = "allarea"
clip_area_shp = "../shp/clip_area/clip.shp"
temp_shp1 = "C:/GIS/T1.shp"
clipped_dataset = "./intermediate/clipped_dataset.shp"
clipped_dataset_f = "./intermediate/clipped_dataset_f.shp"
clipped_dataset_pt = "./intermediate/pt_clipped_dataset.shp"

network_dataset = "./intermediate/network_dataset.shp"
network_dataset_ND = "./intermediate/network_dataset_ND.nd"

all_dataset = "./intermediate/railway_ln_connected.shp"
all_dataset_ND = "./intermediate/railway_ln_connected_ND.nd"

# csv files
no_routes = "noroutes.csv"
no_tolerance = "notolerance.csv"
no_tolerance_buffer = "notolerancebuffer.csv"

node_coordinate_dict = {}

# getting the names of all the shape files
intermediate_folder = './intermediate/'
list_of_shp = os.listdir(intermediate_folder)
list_of_shp = [x for x in list_of_shp if '.shp' in x]
exclude_files_list = ['pt', 'ND_Junctions', '_dataset', 'xml', 'lock']
for filename in exclude_files_list:
    list_of_shp = [x for x in list_of_shp if filename not in x]

list_of_shp = [intermediate_folder + x for x in list_of_shp]
print("List of layers imported {0}".format(list_of_shp))


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


def str_to_list(value):
    new = value.replace("(", "").replace(")", "")
    new = new.split(",")
    return new


# create clip shp
if len(clip_state_list) == 0:
    clip_area_shp = all_area_shp
else:
    arcpy.arcpy.MakeFeatureLayer_management(all_area_shp, all_area_shp_f)
    where_clause = get_where_clause("ABBR", clip_state_list)
    arcpy.SelectLayerByAttribute_management(all_area_shp_f, "NEW_SELECTION", where_clause)
    arcpy.CopyFeatures_management(all_area_shp_f, clip_area_shp)

# read csv files
coordinates_df = pandas.read_csv("tocsv.csv").set_index('Unnamed: 0')
coordinates_df = coordinates_df.fillna("?")
coordinates_df = coordinates_df.applymap(str)
coordinates_df = coordinates_df.applymap(str_to_list)
coordinates_df['new'] = coordinates_df['0'] + coordinates_df['1'] + coordinates_df['2']
coordinates_df = coordinates_df[['new']]
coordinates_dict = coordinates_df.to_dict()['new']

coordinates_conv_dict = {}
for key, value in coordinates_dict.iteritems():
    value1 = value
    if '?' in value1:
        value1.remove('?')
        try:
            value1.remove('?')
        except:
            pass
    if len(value1) == 2:
        value1 = [list((float(value1[0]), float(value1[1])))]
        # print "2:{0}".format(value1)
    elif len(value1) == 4:
        new = [list((float(value1[0]), float(value1[1])))]
        new.append(list((float(value1[2]), float(value1[3]))))
        value1 = new
        # print "4:{0}".format(value1)
    elif len(value1) == 6:
        new = [list((float(value1[0]), float(value1[1])))]
        new.append(list((float(value1[2]), float(value1[3]))))
        new.append(list((float(value1[4]), float(value1[5]))))
        value1 = new
        # print "6:{0}".format(value1)
    else:
        print value1
        print "Exception"
        value1 = []
    coordinates_conv_dict[int(key)] = value1

# base is the one with the highest number of features
count = 0
for shp in list_of_shp:
    count_in_shp = int(arcpy.GetCount_management(shp)[0])
    if count_in_shp > count:
        base = shp
        count = count_in_shp

others = list_of_shp
others.remove(base)


def create_buffer_nd_shp(key, _a_, _b_, _len_):
    print "{0}:{1}->{2}".format(key, _a_, _b_)
    # prepare ND
    # use the key to buffer/clip/create ND
    where_clause = """ "_ID_" = %d""" % key
    arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
    arcpy.Buffer_analysis(other_f, buffer_shp, str(buffer_dist) + ' feet')

    arcpy.SelectLayerByLocation_management(base_f, "INTERSECT", buffer_shp, "", "", "")
    arcpy.CopyFeatures_management(base_f, network_dataset)
    arcpy.BuildNetwork_na(network_dataset_ND)
    return (coordinates_conv_dict[_a_], coordinates_conv_dict[_b_])


# functions
def get_length_route(points):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(arcpy.SpatialReference(4326))
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    arcpy.AddLocations_na("Route", "Stops", m, "Name Name #", "0.5 Miles", "", "", "MATCH_TO_CLOSEST", "CLEAR",
                          "NO_SNAP", "10 Meters", "INCLUDE", "")
    arcpy.Solve_na("Route", "SKIP", "TERMINATE", "500 Kilometers")
    arcpy.SelectData_management("Route", "Routes")
    arcpy.FeatureToLine_management("Route\\Routes", f, "", "ATTRIBUTES")
    leng = [row.getValue("Total_Leng") for row in arcpy.SearchCursor(f)][0] / 1609.34
    return leng


def get_route_distance(a_list, b_list, ND):
    arcpy.MakeRouteLayer_na(ND, "Route", "Length")
    for x1y1 in a_list:
        for x2y2 in b_list:
            try:
                route_leng = get_length_route([x1y1, x2y2])
            except:
                route_leng = 99999
            distance_list_dict.append(route_leng)
    minimum_distance = min(distance_list_dict)
    return minimum_distance


arcpy.CheckOutExtension("Network")

for other in others:
    # clip the area (would be removed later when working with entire US)
    arcpy.MakeFeatureLayer_management(other, "temp")
    arcpy.SelectLayerByLocation_management("temp", "INTERSECT", clip_area_shp, "", "", "")  # takes a long time
    arcpy.CopyFeatures_management("temp", clipped_dataset)
    other_pt = other
    other_pt = other_pt.replace("intermediate/", "intermediate/pt_")
    clipped_dataset_pt = other_pt
    print("Clipped Dataset Created..")
    arcpy.MakeFeatureLayer_management(base, base_f)
    print ("working on {0}".format(other))
    arcpy.MakeFeatureLayer_management(other, other_f)
    start_end_ids_dict = {row1.getValue("_ID_"): [row1.getValue("_A_"), row1.getValue("_B_"), row1.getValue("_LEN_")]
                          for row1 in arcpy.SearchCursor(clipped_dataset)}
    # print clipped_dataset_pt
    # node_coordinate_dict = {row2.getValue("_ID_"): [row2.getValue("_X_"), row2.getValue("_Y_")] for row2 in arcpy.SearchCursor(clipped_dataset_pt)}
    route_not_found_dict = {}
    route_tolerance_exceed_dict = {}
    route_buffer_exceed_dict = {}
    miniature_links_dict = {}

for key in start_end_ids_dict.keys():
    _a_ = start_end_ids_dict[key][0]
    _b_ = start_end_ids_dict[key][1]
    _len_ = start_end_ids_dict[key][2]
    # if any of these nodes are not in the list, just ouput
    if _a_ not in coordinates_conv_dict or _b_ not in coordinates_conv_dict:
        route_not_found_dict[key] = _len_
        continue
    if _len_ < 2 * buffer_dist / 5280:  # if the links are comparable in size to the buffer distance
        miniature_links_dict[key] = _len_
        continue

    # for search of routes within buffer
    (a_list, b_list) = create_buffer_nd_shp(key, _a_, _b_, _len_)
    distance_list_dict = []
    minimum_distance = get_route_distance(a_list, b_list, network_dataset_ND)
    if minimum_distance == 99999:  # any route not found in the buffer layer
        minimum_distance = get_route_distance(a_list, b_list, all_dataset_ND)
        route_buffer_exceed_dict[key] = [minimum_distance, _len_]
        if minimum_distance == 99999:
            route_not_found_dict[key] = _len_
    else:
        route_tolerance_exceed_dict[key] = [minimum_distance, _len_]

pandas.DataFrame.from_dict(route_not_found_dict, orient='index').to_csv(no_routes)
pandas.DataFrame.from_dict(route_tolerance_exceed_dict, orient='index').to_csv(no_tolerance)
pandas.DataFrame.from_dict(route_buffer_exceed_dict, orient='index').to_csv(no_tolerance_buffer)

# create no_route_shp
where_clause = get_where_clause("_ID_", route_not_found_dict.keys())
arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(other_f, output_no_routes_shp)

# create no_tolerance_within_buffer shp
route_within_threshold_dict = {x: y for x, y in route_tolerance_exceed_dict.iteritems() if
                                           abs(y[0] - y[1]) / y[1] > threshold / 100}
where_clause = get_where_clause("_ID_", route_within_threshold_dict.keys())
arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(other_f, output_tolerance_exceed_shp)
arcpy.AddField_management(output_tolerance_exceed_shp, '_RLENG_', "FLOAT")
with arcpy.da.UpdateCursor(output_tolerance_exceed_shp, ['_ID_', '_RLENG_']) as cursor:
    for row in cursor:
        row[1] = route_within_threshold_dict[row[0]][0]
        cursor.updateRow(row)

#create no_tolerance_shp
route_buffer_within_threshold_dict = {x: y for x, y in route_buffer_exceed_dict.iteritems() if
                                           abs(y[0] - y[1]) / y[1] > threshold / 100}
where_clause = get_where_clause("_ID_", route_buffer_within_threshold_dict.keys())
arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(other_f, output_buffer_tolerance_exceed_shp)
arcpy.AddField_management(output_buffer_tolerance_exceed_shp, '_RLENG_', "FLOAT")
with arcpy.da.UpdateCursor(output_buffer_tolerance_exceed_shp, ['_ID_', '_RLENG_']) as cursor:
    for row in cursor:
        row[1] = route_buffer_within_threshold_dict[row[0]][0]
        cursor.updateRow(row)