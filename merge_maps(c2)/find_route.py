# finding links that are not in base network
# 1. at least one of the nodes could not be snapped within snap distance, or no route found
# 2. route found within buffer distance
# 3. routes found within the network

import arcpy
import pandas
import os
from merge import *

no_tolerance_buffer_dist = "1000 feet"

arcpy.env.overwriteOutput = True
other = "./intermediate/NARN_LINE_03162018.shp"
base = "./intermediate/railway_ln_connected.shp"
other_f = "other_f"
base_f = "base_f"
arcpy.MakeFeatureLayer_management(base, base_f)
arcpy.MakeFeatureLayer_management(other, other_f)

# parameters
a_list = []
b_list = []

node_coordinate_dict = {}

def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


def str_to_list(value):
    new = value.replace("(", "").replace(")", "")
    new = new.split(",")
    return new


# read csv files
coordinates_df = pandas.read_csv(node_coordinates_dict).set_index('Unnamed: 0')
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


def create_buffer_nd_shp(key, _a_, _b_, _len_):
    # prepare ND
    # use the key to buffer/clip/create ND
    where_clause = """ "_ID_" = %d""" % key
    arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
    #arcpy.Buffer_analysis(other_f, buffer_shp, str(buffer_dist_list[-1]) + ' feet')
    arcpy.Buffer_analysis(other_f, buffer_shp, no_tolerance_buffer_dist)
    arcpy.Clip_analysis(base, buffer_shp, network_dataset)
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
    arcpy.AddLocations_na(route_f, "Stops", m, "Name Name #", "0.5 Miles", "", "", "MATCH_TO_CLOSEST", "CLEAR",
                          "NO_SNAP", "10 Meters", "INCLUDE", "")
    arcpy.Solve_na(route_f, "SKIP", "TERMINATE", "500 Kilometers")
    arcpy.SelectData_management(route_f, "Routes")
    arcpy.FeatureToLine_management(route_f + "\\Routes", f, "", "ATTRIBUTES")
    # corrected to "Total_Length" from "Total_Leng"
    leng = [row.getValue("Total_Length") for row in arcpy.SearchCursor(f)][0] / 1609.34
    return leng


def get_route_distance(a_list, b_list, ND):
    arcpy.MakeRouteLayer_na(ND, route_f, "Length")
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
start_end_ids_dict = {row1.getValue("_ID_"): [row1.getValue("_A_"), row1.getValue("_B_"), row1.getValue("_LEN_")]
                      for row1 in arcpy.SearchCursor(other)}
# print clipped_dataset_pt
route_not_found_or_not_identified_dict = {}
route_found_within_network_dict = {}
route_found_within_buffer_dict = {}
miniature_links_dict = {}  # not written in a file as of now
arcpy.BuildNetwork_na(all_dataset_ND)

for link_id in start_end_ids_dict.keys():
    _a_ = start_end_ids_dict[link_id][0]
    _b_ = start_end_ids_dict[link_id][1]
    _len_ = start_end_ids_dict[link_id][2]
    print "{0}:{1}->{2}".format(link_id, _a_, _b_)
    # if any of these nodes are not in the list, just ouput
    if _a_ not in coordinates_conv_dict or _b_ not in coordinates_conv_dict:
        route_not_found_or_not_identified_dict[link_id] = _len_
        print "!"  # one or more of the nodes not in base network
        continue
    if _len_ < 2 * buffer_dist / 5280:  # if the links are comparable in size to the buffer distance
        miniature_links_dict[link_id] = _len_
        print "~"  # length of the link is too small compared to buffer
        continue
    # for search of routes within buffer
    (a_list, b_list) = create_buffer_nd_shp(link_id, _a_, _b_, _len_)
    distance_list_dict = []
    minimum_distance = get_route_distance(a_list, b_list, network_dataset_ND)
    if minimum_distance == 99999:  # any route not found in the buffer layer
        minimum_distance = get_route_distance(a_list, b_list, all_dataset_ND)
        if minimum_distance == 99999:
            route_not_found_or_not_identified_dict[link_id] = _len_
            print "^"  # nodes mapped but route not found in base network
        else:
            print "&"  # route not found within buffer
            route_found_within_network_dict[link_id] = [minimum_distance, _len_]
    else:
        print "@"
        route_found_within_buffer_dict[link_id] = [minimum_distance, _len_]

pandas.DataFrame.from_dict(route_not_found_or_not_identified_dict, orient='index').to_csv(no_routes)
pandas.DataFrame.from_dict(route_found_within_network_dict, orient='index').to_csv(no_tolerance)
pandas.DataFrame.from_dict(route_found_within_buffer_dict, orient='index').to_csv(no_tolerance_buffer)
pandas.DataFrame.from_dict(miniature_links_dict, orient='index').to_csv(miniature_links)

#pandas.DataFrame.from_dict(start_end_ids_dict, orient='index').to_csv("apple.csv")
