#work on IDs not FIDs, IDs never change, FIDs do
import pandas
import arcpy
import os
import sys  # for printing . :D
from parameters import *

old_n = old_nodes_shp
new_n = new_nodes_shp
old_l = old_links_cropped_shp
new_l = new_links_clipped
old_ns = snapped_old_nodes






arcpy.env.overwriteOutput = True  # overwrite files if its already present
arcpy.CheckOutExtension("Network")

#remove the nodes that are not connected to anyone
arcpy.MakeFeatureLayer_management(old_ns, "snapped")
arcpy.SelectLayerByLocation_management("snapped", "INTERSECT", new_l, "", "NEW_SELECTION", "INVERT")
isolated_ids = [f[0] for f in arcpy.da.SearchCursor("snapped", 'ID')]

#first new network layer
arcpy.CheckOutExtension("Network")
arcpy.BuildNetwork_na(B1_ND)
#print("Network Rebuilt")
arcpy.MakeRouteLayer_na(B1_ND, B1_route, "Length")


#how far is the nearest node (old network)
def get_near_node_dict(nodelayer):
    arcpy.Project_management(nodelayer, temp1, arcpy.SpatialReference(102039))
    arcpy.Near_analysis(temp1, temp1)
    near_node_dict = {row.getValue("ID"): [row.getValue("NEAR_Fid"), row.getValue("NEAR_DIST") / 1609.34] for row in
                      arcpy.SearchCursor(temp1)}
    id_fid_dict = {row.getValue("FID"): row.getValue("ID") for row in arcpy.SearchCursor(temp1)}
    near_node_dict = {x:y for x,y in near_node_dict.iteritems()}
    return near_node_dict


# nodeA and NodeB are integers
# def get_distance(nodeAlayer, nodeBlayer, nodeAColumnName, nodeBColumnName, nodeA, nodeB):
#     # create a set of origin and destination FIPS to be loaded in the network analyst
#     sys.stdout.write('#')
#     arcpy.Select_analysis(nodeAlayer, o, '{0} = {1}'.format(nodeAColumnName, nodeA))
#     arcpy.Select_analysis(nodeBlayer, d, '{0} = {1}'.format(nodeBColumnName, nodeB))
#     arcpy.Merge_management([o, d], m)
#     arcpy.AddLocations_na(B1_route, "Stops", m, "Name Name #", near_snap_dist, "", "B1 SHAPE;B1_ND_Junctions SHAPE",
#                           "MATCH_TO_CLOSEST", "CLEAR", "NO_SNAP", near_snap_dist, "INCLUDE", "B1 #;B1_ND_Junctions #")
#     try:
#         arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", near_snap_dist)
#         arcpy.SelectData_management(B1_route, "Routes")
#         arcpy.FeatureToLine_management(B1_route+"/Routes", feature, "", "ATTRIBUTES")
#     except:
#         return 999999
#     return ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH')][0])

def get_distance(points):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(arcpy.SpatialReference(4326))
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    arcpy.AddLocations_na(B1_route, "Stops", m, "Name Name #", "2 Miles", "", "", "MATCH_TO_CLOSEST", "CLEAR", "NO_SNAP", "500 Meters", "INCLUDE", "")
    try:
        arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", near_snap_dist)
        arcpy.SelectData_management(B1_route, "Routes")
        arcpy.FeatureToLine_management(B1_route+"/Routes", feature, "", "ATTRIBUTES")
    except:
        return 999999
    return ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH')][0])



# (ID, nodeLayer, columnName)=(1538, new_n, "Fid")
def get_buffer_nodes_ids(ID):
    local_buffer_dist = buffer_dist
    if near_node_dict[ID][1] < local_buffer_dist: #the buffer distance cannot be more than the distance to nearest node
        local_buffer_dist = near_node_dict[ID][1]
        print("Buffer Distance changed to {0} Miles".format(local_buffer_dist))
    if local_buffer_dist == 0:
        local_buffer_dist = 0.1  # minimum value for buffer distance
    # create a circular buffer of given miles
    arcpy.Select_analysis(old_n, temp, '{0} = {1}'.format("ID", ID))
    arcpy.Buffer_analysis(temp, temp1, "{0} Miles".format(local_buffer_dist), "FULL", "ROUND", "NONE", "", "PLANAR")
    # find nodes around that buffer
    arcpy.MakeFeatureLayer_management(new_n, 'feature_lyr')
    arcpy.SelectLayerByLocation_management('feature_lyr', "WITHIN", temp1, "", "NEW_SELECTION", "NOT_INVERT")
    list_of_ids = [row.getValue("_ID_") for row in arcpy.SearchCursor('feature_lyr')] #this is the ID of the new network
    return list_of_ids


#links = old_links_shp
def get_old_node_connections_dict(links):
    arcpy.FeatureVerticesToPoints_management(links, temp1, "BOTH_ENDS")
    arcpy.SpatialJoin_analysis(temp1, old_n, temp2, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST")
    nearfid_to_fips_fid = [[row.getValue("ORIG_FID"), row.getValue("ID_1")] for row in arcpy.SearchCursor(temp2)]
    #node_fid_id_dict = {row.getValue("ID"): row.getValue("FID") for row in arcpy.SearchCursor(old_n)}
    a = {}
    for linkid, nodeid in nearfid_to_fips_fid:
        a.setdefault(linkid,[]).append(nodeid)
    b = a.values()
    node_node_dict = {}
    for node1,node2 in b:
        node_node_dict.setdefault(node1,[]).append(node2)
        node_node_dict.setdefault(node2, []).append(node1)
    return node_node_dict

def get_coordinates(link, id):
    new_dict = {}
    with arcpy.da.SearchCursor(link, [id,"SHAPE@XY"]) as curs:
        for _id_,xy in curs:
            new_dict[_id_]=xy
    return new_dict


# get the dict of all near nodes and their distance (used for smaller distances to modify local buffer distance)
near_node_dict = get_near_node_dict(old_n)

# this is the dictionary that connects old_n and new nodes
old_new_node_dictionary = {}

# dictionary of all connections between each node (in old network)
old_node_connections_dict = get_old_node_connections_dict(old_l)

# the program begins here
new_node_id_coordinates_dict = get_coordinates(new_n, "_ID_")
old_node_id_coordinates_dict = get_coordinates(old_ns, "ID")


route_not_found_dict = {}
multiple_minimum = {}

for row in arcpy.da.SearchCursor(old_ns, ["ID"]):
    current_id = row[0]
    if current_id in isolated_ids:
        continue
    #get FID as row[0]
    print "Old Node ID: {0}".format(current_id)
    ids_distance_dict = {}
    buffer_node_ids = get_buffer_nodes_ids(current_id)
    print "{0}: {1}".format(current_id,buffer_node_ids)
    if len(buffer_node_ids) in [0, 1]:  # if no or 1 node nearby (no need to run)
        if len(buffer_node_ids) == 0:
            old_new_node_dictionary[current_id] = "" #did not find any within buffer
            continue
        else:  # if exactly one node found, that node is where the old node is supposed to snap
            old_new_node_dictionary[current_id] = buffer_node_ids[0]
            continue
    ids_of_connecting_nodes = old_node_connections_dict[current_id]
    ids_of_connecting_nodes = list(set([x for x in ids_of_connecting_nodes if x not in isolated_ids]))
    print("\tIDs of connecting nodes: {0}".format(ids_of_connecting_nodes)) # in old network
    #remove the buffer_node_ids that are not in the snapped_removed_ids

    #buffer_node_ids
    for buffer_id in buffer_node_ids:
        #print ("\tworking on: {0}".format(buffer_id)) #buffer node id
        ids_distance_dict[buffer_id] = 0
        dist = 0
        for id in ids_of_connecting_nodes:
            pair = new_node_id_coordinates_dict[buffer_id], old_node_id_coordinates_dict[id]
            currdist = get_distance(pair)
            if currdist == 999999:
                route_not_found_dict[buffer_id] = id
            dist += currdist
        ids_distance_dict[buffer_id] = dist
        ids_distance_dict[buffer_id] = dist

    # choosing the one with minimum distance
    for key, values in ids_distance_dict.iteritems():  # print id and distance formatted
        print ("\t\t{0}: {1}".format(key, values))
    minimum = min(ids_distance_dict.values())
    maximum = max(ids_distance_dict.values())
    if minimum == maximum:
        old_new_node_dictionary[current_id] = -99 #all the nodes have the same distance, or cannot be solved in all
    all_minimum_nodes = [k for k, v in ids_distance_dict.items() if v == minimum]

    if len(all_minimum_nodes) == 1: #snap to that
        old_new_node_dictionary[current_id] = all_minimum_nodes[0]
        print ("Added to snap dictionary: {0}:{1}".format(current_id, old_new_node_dictionary[current_id]))
    else:
        multiple_minimum[current_id] = all_minimum_nodes


pandas.DataFrame.from_dict(old_new_node_dictionary, orient='index').to_csv(old_new_csv)
pandas.DataFrame.from_dict(route_not_found_dict, orient='index').to_csv(route_not_found_csv)
pandas.DataFrame.from_dict(multiple_minimum, orient='index').to_csv(multiple_minimum_csv)


print("Node Conversion complete")