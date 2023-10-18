# finding links that are not in base network
# 1. at least one of the nodes could not be snapped within snap distance, or no route found
# 2. route found within buffer distance
# 3. routes found within the network

import arcpy
import pandas
import os
import numpy as np
from math import isnan
from merge import *
import multiprocessing
from functools import partial
import pandas as pd


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


def str_to_list(value):
    new = value.replace("(", "").replace(")", "")
    new = new.split(",")
    return new


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
    distance_list = []
    arcpy.MakeRouteLayer_na(ND, route_f, "Length")
    for x1y1 in a_list:
        for x2y2 in b_list:
            try:
                route_leng = get_length_route([x1y1, x2y2])
            except:
                route_leng = 99999
            distance_list.append(route_leng)
    minimum_distance = min(distance_list)
    return minimum_distance


def get_type(coordinates_conv_dict, start_end_ids_dict,  other, base, link_id):
    _a_ = start_end_ids_dict[link_id][0]
    _b_ = start_end_ids_dict[link_id][1]
    _len_ = start_end_ids_dict[link_id][2]
    print "{0}:{1}->{2}".format(link_id, _a_, _b_)
    # if any of these nodes are not in the list, just ouput
    if _a_ not in coordinates_conv_dict or _b_ not in coordinates_conv_dict:
        #route_not_found_or_not_identified_dict[link_id] = _len_
        return _len_, np.nan, 1  # one or more of the nodes not in base network
    if _len_ < 2 * buffer_dist / 5280:  # if the links are comparable in size to the buffer distance
        #miniature_links_dict[link_id] = _len_
        return _len_, np.nan, 4  # length of the link is too small compared to buffer
    # prepare ND
    # use the key to buffer/clip/create ND
    #network_dataset_ND = "in_memory/ND1"
    other_f = "other_f"
    arcpy.MakeFeatureLayer_management(other, other_f)
    no_tolerance_buffer_dist = "1000 feet"
    where_clause = """ "_ID_" = %d""" % link_id
    arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
    arcpy.Buffer_analysis(other_f, buffer_shp, no_tolerance_buffer_dist)
    arcpy.Clip_analysis(base, buffer_shp, network_dataset)
    #arcpy.na.CreateNetworkDataset("in_memory_n1", network_dataset_ND, "", "NO_ELEVATION" )
    arcpy.BuildNetwork_na(network_dataset_ND)
    (a_list, b_list) = (coordinates_conv_dict[_a_], coordinates_conv_dict[_b_])
    minimum_distance = get_route_distance(a_list, b_list, network_dataset_ND)
    if minimum_distance == 99999:  # any route not found in the buffer layer
        minimum_distance = get_route_distance(a_list, b_list, all_dataset_ND)
        if minimum_distance == 99999:
            #route_not_found_or_not_identified_dict[link_id] = _len_
            return _len_, np.nan, 1  # nodes mapped but route not found in base network
        else:
            #route_found_within_network_dict[link_id] = [minimum_distance, _len_]
            return _len_, minimum_distance, 2  # route not found within buffer
    else:
        #route_found_within_buffer_dict[link_id] = [minimum_distance, _len_]
        return _len_, minimum_distance, 3  # routes found within buffer



def main():
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Network")
    coordinates_conv_dict = np.load('./intermediate/node_coord_dict.npy').item()
    coordinates_conv_dict = {x: y for x, y in coordinates_conv_dict.iteritems() if not str(y) == "(nan, nan)"}
    other = "./intermediate/NARN_LINE_03162018.shp"
    base = "./intermediate/railway_ln_connected.shp"
    # parameters
    start_end_ids_dict = {row1.getValue("_ID_"): [row1.getValue("_A_"), row1.getValue("_B_"), row1.getValue("_LEN_")]
                          for row1 in arcpy.SearchCursor(other)}
    link_ids = start_end_ids_dict.keys()
    #link_ids = link_ids[0:5]
    #arcpy.BuildNetwork_na(all_dataset_ND)

    # pool = multiprocessing.Pool()
    # func = partial(get_type, coordinates_conv_dict, start_end_ids_dict, other, base)
    # route_list = pool.map(func, link_ids)
    # pool.close()
    # pool.join()
    #link_route_type_dict = {x: y for x, y in zip(link_ids, route_list)}

    link_route_type_dict = {}
    for id in link_ids:
        link_route_type_dict[id] = get_type(coordinates_conv_dict, start_end_ids_dict,  other, base, id)



    pd.DataFrame({key: pd.Series(value) for key, value in link_route_type_dict.iteritems()}).transpose().to_csv(
        "./csv/link_route_type_dict.csv")
    np.save('./intermediate/link_route_type_dict', np.array(dict(link_route_type_dict)))


if __name__ == '__main__':
    main()
