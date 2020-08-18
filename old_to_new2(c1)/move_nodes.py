# work on IDs not FIDs, IDs never change, FIDs do
import pandas
import arcpy
from parameters import *
import random
import numpy as np
import os




def get_distance(points):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(sr_g)
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    arcpy.AddLocations_na(B1_route, "Stops", m, "Name Name #", "0 Miles", "", "", "MATCH_TO_CLOSEST", "CLEAR",
                          "NO_SNAP", "0 Miles", "INCLUDE", "")  # just in case
    try:
        arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", "")
        arcpy.SelectData_management(B1_route, "Routes")
        arcpy.FeatureToLine_management(B1_route + "/Routes", feature, "", "ATTRIBUTES")
    except:
        return 999999
    try:
        arcpy.Append_management(feature, empty_memory)
    except:
        arcpy.CopyFeatures_management(feature, empty_memory)
    return ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH')][0]) / 1604.34


def get_dist(points, current_id, buffer_id):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(sr_g)
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    arcpy.AddLocations_na(B1_route, "Stops", m, "Name Name #", "0 Miles", "", "", "MATCH_TO_CLOSEST", "CLEAR",
                          "NO_SNAP", "0 Miles", "INCLUDE", "")  # just in case
    try:
        arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", "")
        arcpy.SelectData_management(B1_route, "Routes")
        arcpy.FeatureToLine_management(B1_route + "/Routes", feature, "", "ATTRIBUTES")
    except:
        print "Cannot Solve"
        return [], 999999
    arcpy.AddField_management(feature, "curr_id", "LONG")
    arcpy.AddField_management(feature, "buffer_id", "LONG")
    arcpy.CalculateField_management(feature, "curr_id", current_id, "PYTHON")
    arcpy.CalculateField_management(feature, "buffer_id", buffer_id, "PYTHON")
    arcpy.SelectLayerByLocation_management("newlf", "WITHIN", feature)
    _list_ = [f[0] for f in arcpy.da.SearchCursor("newlf", '_ID_')]
    return _list_, ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH', "", sr_p)][0]) / 1604.34


# creates links in GIS and returns linkIDs
def get_distance1(ids_of_connecting_nodes, current_id, buffer_id):
    no_overlapping_found_flag = 0
    dist = 0
    count_dict = {}
    for id in ids_of_connecting_nodes:
        pair = new_node_id_coordinates_dict[buffer_id], old_node_id_coordinates_dict[id]
        list_of_links, currdist = get_dist(pair, current_id, buffer_id)
        if currdist == 999999:
            route_not_found_dict[buffer_id] = id
        dist += currdist
        for link in list_of_links:
            if link in count_dict:
                count_dict[link] = count_dict[link] + 1
            else:
                count_dict[link] = 1
    try:
        id, max_count = sorted(count_dict.items(), key=lambda item: item[1])[-1]
    except:
        return dist, 0
    if max_count == 1:  # only the routes that are not overlapped (the size of the shapefile is limited)
        no_overlapping_found_flag = 1
        # comment this if you dont want a shapefile
        # try:
        #    arcpy.Append_management(feature, empty_memory)
        # except: #if its the first time
        #     arcpy.CopyFeatures_management(feature, empty_memory)
    return dist, no_overlapping_found_flag


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


def get_id_mnsod(current_id):
    print("Old Node ID: {0}".format(current_id))
    if current_id in all_ids_dist_dict:
        ids_distance_dict = all_ids_dist_dict[current_id]
    else:
        ids_distance_dict = {}  # each id and its sum of distances to connecting nodes on all buffers
    buffer_nodes = curnod_buffnod_dist_dict[current_id]
    sorted_buffer_nodes = sorted(buffer_nodes.items(), key=lambda item: item[1])
    print("{0}: {1}".format(current_id, sorted_buffer_nodes))
    ids_of_connecting_nodes = old_node_connections_dict[current_id]
    # the isolated nodes is removed because there would be no route to the node (saves time)
    #ids_of_connecting_nodes = list(set([x for x in ids_of_connecting_nodes if x not in isolated_ids]))
    print("\tIDs of connecting nodes: {0}".format(ids_of_connecting_nodes))  # in old network
    # remove the buffer_node_ids that are not in the snapped_removed_ids
    # buffer_node_ids
    count = 0
    for buffer_id, distance in sorted_buffer_nodes:
        if distance > near_node_dict[current_id][1] * 2:  # cannot be too close
            break
        if buffer_id in ids_distance_dict:
            print ("sum of paths known for bufferid: {0}".format(buffer_id))
            continue
        else:  # id not present (check if further going necessary
            dist1, overlap_flag = get_distance1(ids_of_connecting_nodes, current_id, buffer_id)
            ids_distance_dict[buffer_id] = [dist1, overlap_flag]
    return ids_distance_dict
    # save dictionaries as numpy objects


def main():
    # retrieve values
    filenames_list = os.listdir("./intermediate/")
    for filename in filenames_list:
        var_name = filename.split(".")[0]
        print ((var_name + " = np.load('./intermediate/" + filename + "')"))
        exec (var_name + " = np.load('./intermediate/" + filename + "').item()") in globals()
    # for randomness
    connections_gt3_list = [x for x, y in old_node_connections_dict.iteritems() if len(y) > 2]
    curr_ids = connections_gt3_list
    for current_id in curr_ids:
        all_ids_dist_dict[current_id] = get_id_mnsod(current_id)
        np.save('./intermediate/all_ids_dist_dict', np.array(dict(all_ids_dist_dict)))
    # outputs
    count_connections = {x: len(y) for x, y in old_node_connections_dict.iteritems()}
    np.save('./intermediate/count_connections', np.array(dict(count_connections)))
    np.save('./intermediate/nearest_ground_truth_dict', np.array(dict(nearest_ground_truth_dict)))
    np.save('./intermediate/ids_nearids_dist_dict', np.array(dict(ids_nearids_dist_dict)))





if __name__ == "__main__":
    all_ids_dist_dict = {}
    route_not_found_dict = {}
    m = "in_memory/m11"
    arcpy.env.overwriteOutput = True
    old_n = old_nodes_shp
    new_n = new_nodes_shp
    old_l = old_links_shp
    new_l = new_links_clipped
    old_ns = snapped_old_nodes
    new_ngt = "../../RAIL11/RAIL/gis/allnodes.shp"
    empty = "C:/gis/empty.shp"
    empty_memory = "in_memory/e1"
    memory_1 = "in_memory/m1"
    memory_2 = "in_memory/m2"
    arcpy.CopyFeatures_management(empty, empty_memory)
    arcpy.CheckOutExtension("Network")
    # arcpy.BuildNetwork_na(B1_ND)
    arcpy.MakeRouteLayer_na(B1_ND, B1_route, "Length")
    arcpy.MakeFeatureLayer_management(new_l, "newlf")
    sr_p = arcpy.SpatialReference(102039)
    sr_g = arcpy.SpatialReference(4326)
    main()
