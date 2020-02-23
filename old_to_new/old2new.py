# work on IDs not FIDs, IDs never change, FIDs do
import pandas
import arcpy
import os
import sys  # for printing . :D
from parameters import *
import random






old_n = old_nodes_shp
new_n = new_nodes_shp
old_l = old_links_shp
new_l = new_links_clipped
old_ns = snapped_old_nodes
new_ngt = "../../RAIL11/RAIL/gis/allnodes.shp"
empty = "C:/gis/empty.shp"
empty_memory = "in_memory/e1"
arcpy.CopyFeatures_management(empty, empty_memory)

arcpy.env.overwriteOutput = True  # overwrite files if its already present
arcpy.CheckOutExtension("Network")
arcpy.BuildNetwork_na(B1_ND)
arcpy.MakeRouteLayer_na(B1_ND, B1_route, "Length")


# how far is the nearest node (old network)
def get_near_node_dict(nodelayer):
    arcpy.Project_management(nodelayer, temp1, arcpy.SpatialReference(102039))
    arcpy.Near_analysis(temp1, temp1)
    near_node_dict = {row.getValue("ID"): [row.getValue("NEAR_Fid"), row.getValue("NEAR_DIST") / 1609.34] for row in
                      arcpy.SearchCursor(temp1)}
    id_fid_dict = {row.getValue("FID"): row.getValue("ID") for row in arcpy.SearchCursor(temp1)}
    near_node_dict = {x: y for x, y in near_node_dict.iteritems()}
    return near_node_dict

def get_distance(points):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(arcpy.SpatialReference(4326))
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    arcpy.AddLocations_na(B1_route, "Stops", m, "Name Name #", "0 Miles", "", "", "MATCH_TO_CLOSEST", "CLEAR", "NO_SNAP", "0 Meters", "INCLUDE", "")
    try:
        arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", "1 Meters")
        arcpy.SelectData_management(B1_route, "Routes")
        arcpy.FeatureToLine_management(B1_route + "/Routes", feature, "", "ATTRIBUTES")
    except:
        return 999999
    try:
        arcpy.Append_management(feature, empty_memory)
    except:
        arcpy.CopyFeatures_management(feature, empty_memory)
    return ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH')][0])


# (ID, nodeLayer, columnName)=(1538, new_n, "Fid")
def get_buffer_nodes_ids(ID):
    local_buffer_dist = buffer_dist
    if near_node_dict[ID][1] < local_buffer_dist:  # the buffer distance cannot be more than the distance to nearest node
        local_buffer_dist = near_node_dict[ID][1]
        print("Buffer Distance changed to {0} Miles".format(local_buffer_dist))
    if local_buffer_dist == 0:
        local_buffer_dist = 0.1  # minimum value for buffer distance
    # create a circular buffer of given miles
    arcpy.Select_analysis(old_n, temp, '{0} = {1}'.format("ID", ID))
    #arcpy.Buffer_analysis(temp, temp1, "{0} Miles".format(local_buffer_dist), "FULL", "ROUND", "NONE", "", "PLANAR")
    # find nodes around that buffer
    arcpy.MakeFeatureLayer_management(new_n, 'feature_lyr')
    arcpy.SelectLayerByLocation_management('feature_lyr', "WITHIN_A_DISTANCE", temp, "{0} Miles".format(local_buffer_dist), "NEW_SELECTION", "")
    # selecting the IDs in the new network
    list_of_ids = [row.getValue("_ID_") for row in arcpy.SearchCursor('feature_lyr')]
    return list_of_ids


# links = old_links_shp
def get_old_node_connections_dict(links):
    arcpy.FeatureVerticesToPoints_management(links, temp1, "BOTH_ENDS")
    arcpy.SpatialJoin_analysis(temp1, old_n, temp2, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST")
    nearfid_to_fips_fid = [[row.getValue("ORIG_FID"), row.getValue("ID_1")] for row in arcpy.SearchCursor(temp2)]
    # node_fid_id_dict = {row.getValue("ID"): row.getValue("FID") for row in arcpy.SearchCursor(old_n)}
    a = {}
    for linkid, nodeid in nearfid_to_fips_fid:
        a.setdefault(linkid, []).append(nodeid)
    b = a.values()
    node_node_dict = {}
    for node1, node2 in b:
        node_node_dict.setdefault(node1, []).append(node2)
        node_node_dict.setdefault(node2, []).append(node1)
    return node_node_dict


def get_coordinates(link, id):
    new_dict = {}
    with arcpy.da.SearchCursor(link, [id, "SHAPE@XY"]) as curs:
        for _id_, xy in curs:
            new_dict[_id_] = xy
    return new_dict


def get_nearest_ground_truth_dict():
    temp = "C:/gis/tempp.shp"
    arcpy.CopyFeatures_management(new_n, temp)
    arcpy.Near_analysis(temp,new_ngt)
    near_dist_dict = {f[0]:f[1] for f in arcpy.da.SearchCursor(temp, ['_ID_', "NEAR_DIST"])}
    return near_dist_dict


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


# find the nodes that are not connected to anyone (aka. did not find any snaps in the new network, could be skipped later)
arcpy.MakeFeatureLayer_management(old_ns, "snapped")
arcpy.SelectLayerByLocation_management("snapped", "INTERSECT", new_l, "", "NEW_SELECTION", "INVERT")
isolated_ids = [f[0] for f in arcpy.da.SearchCursor("snapped", 'ID')]


# get the dict of all near nodes and their distance (used for smaller distances to modify local buffer distance)
near_node_dict = get_near_node_dict(old_n)


# dictionary of all connections between each node (in old network)
old_node_connections_dict = get_old_node_connections_dict(old_l)


# the program begins here
new_node_id_coordinates_dict = get_coordinates(new_n, "_ID_")
old_node_id_coordinates_dict = get_coordinates(old_ns, "ID")



#for randomness
connections_gt3_list = [x for x,y in old_node_connections_dict.iteritems() if len(y)>2 ]


route_not_found_dict = {}
multiple_minimum = {}

buffer_dists = [3,2.5,2,1.5,1,0.5]  # default buffer distance (to find new nodes close to old nodes)
#buffer_dist = 1.5
sample_size = 10
curr_ids = random.sample(connections_gt3_list, sample_size)
curr_ids = connections_gt3_list
all_dict = {}

arcpy.Delete_management(empty_memory)

for buffer_dist in buffer_dists:
    old_new_node_dictionary = {}
    for current_id in curr_ids:
        # if current_id in isolated_ids:
        #     old_new_node_dictionary[current_id] = -98 #dangling nodes
        #     continue
        # get FID as row[0]
        print "Old Node ID: {0}".format(current_id)
        ids_distance_dict = {}
        buffer_node_ids = get_buffer_nodes_ids(current_id)
        if current_id in all_dict:  #if any big distance buffer confirmed that node, no need to do that work again,
            for value in all_dict[current_id]:
                if value in buffer_node_ids:
                    old_new_node_dictionary[current_id] = value
                    print ("this node was already found at a higher buffer distance.. logged")
                    break #getting out of immediate for loop
        if current_id in old_new_node_dictionary:
            continue
        print "{0}: {1}".format(current_id, buffer_node_ids)
        # if len(buffer_node_ids) in [0, 1]:  # if no or 1 node nearby (no need to run)
        #     if len(buffer_node_ids) == 0:
        #         old_new_node_dictionary[current_id] = -97  # did not find any within buffer
        #         continue
        #     else:  # if exactly one node found, that node is where the old node is supposed to snap
        #         old_new_node_dictionary[current_id] = buffer_node_ids[0]
        #         continue
        ids_of_connecting_nodes = old_node_connections_dict[current_id]
        #the isolated nodes is removed because there would be no route to the node (saves time)
        ids_of_connecting_nodes = list(set([x for x in ids_of_connecting_nodes if x not in isolated_ids]))
        print("\tIDs of connecting nodes: {0}".format(ids_of_connecting_nodes))  # in old network
        # if len(ids_of_connecting_nodes) <=2:
        #     old_new_node_dictionary[current_id] = -96  # did not run algorithm because only 2 or less connecting nodes
        #     continue
        # remove the buffer_node_ids that are not in the snapped_removed_ids
        # buffer_node_ids
        for buffer_id in buffer_node_ids:
            # print ("\tworking on: {0}".format(buffer_id)) #buffer node id
            ids_distance_dict[buffer_id] = 0
            dist = 0
            for id in ids_of_connecting_nodes:
                pair = new_node_id_coordinates_dict[buffer_id], old_node_id_coordinates_dict[id]
                currdist = get_distance(pair)
                if currdist == 999999:
                    route_not_found_dict[buffer_id] = id
                dist += currdist
            ids_distance_dict[buffer_id] = dist
        # choosing the one with minimum distance
        for key, values in ids_distance_dict.iteritems():  # print id and distance formatted
            print ("\t\t{0}: {1}".format(key, values))
        if not bool(ids_distance_dict):
            old_new_node_dictionary[current_id] = -96 #no nodes foudn
            continue
        minimum = min(ids_distance_dict.values())
        maximum = max(ids_distance_dict.values())
        if minimum == maximum:
            old_new_node_dictionary[current_id] = -99  # all the nodes have the same distance, or all nodes cannot be solved
        all_minimum_nodes = [k for k, v in ids_distance_dict.items() if v == minimum]
        if len(all_minimum_nodes) == 1:  # snap to that
            old_new_node_dictionary[current_id] = all_minimum_nodes[0]
            print ("Added to snap dictionary: {0}:{1}".format(current_id, old_new_node_dictionary[current_id]))
        else:
            multiple_minimum[current_id] = all_minimum_nodes
    for key,value in old_new_node_dictionary.iteritems():
        all_dict.setdefault(key,[]).append(value)
    #all_df.append(pandas.DataFrame({'dist':[buffer_dist]*len(old_new_node_dictionary), 'old_nodes': old_new_node_dictionary.keys(), 'new_nodes': old_new_node_dictionary.values()}))

# pandas.DataFrame.from_dict(old_new_node_dictionary, orient='index').to_csv(old_new_csv)
# pandas.DataFrame.from_dict(route_not_found_dict, orient='index').to_csv(route_not_found_csv)
# pandas.DataFrame.from_dict(multiple_minimum, orient='index').to_csv(multiple_minimum_csv)
arcpy.CopyFeatures_management(empty_memory, temp)



nearest_ground_truth_dict = get_nearest_ground_truth_dict()



data_df = pandas.DataFrame.from_dict(all_dict, orient='index')
data_df = data_df.dropna(axis=1)
data_df.columns = [buffer_dists]
data_df['dist'] = data_df[3.0].map(nearest_ground_truth_dict)

threshold = "0.001"


list_of_found_nodes = [x for x in data_df[3.0].tolist() if x not in [-99,-98,-97,-96]]

arcpy.MakeFeatureLayer_management(new_n, "newnf")
arcpy.SelectLayerByAttribute_management("newnf", "NEW_SELECTION", get_where_clause("_ID_", list_of_found_nodes))
arcpy.CopyFeatures_management("newnf", temp)
arcpy.Near_analysis(temp,new_ngt)


print("Node Conversion complete")
