import pandas
import arcpy
import os
import sys  # for printing . :D

arcpy.env.overwriteOutput = True  # overwrite files if its already present

buffer_dist = 1.7  # default buffer distance (to find new nodes close to old nodes)
near_snap_dist = "1 Mile"  # the distance to which the old nodes has to snapped to the new network
network_buffer_dist = 5

oldnodes = '../shp/Rail2M/Rail2MNodes.shp'
oldlinks = '../shp/Rail2M/Rail2MNodes.shp'
newlinks = '../shp/railway_ln_connected/railway_ln_connected.shp'


#get new nodes (calculate this)
newnodes = 'assets/new_nodes.shp'
snapped_old_nodes = 'assets/snapped_old_nodes_new_link.shp'



# temporary files
o = "C:/GIS/o.shp"
d = "C:/GIS/d.shp"
m = "C:/GIS.m.shp"
temp = "C:/GIS/temp.shp"
temp1 = "C:/GIS/temp1.shp"
temp2 = "C:/GIS/temp2.shp"


B1_ND = "railway_ln_connected_ND2.nd"
feature = "assets/feature_unlocked_temp.shp"  # i guess this is just a temporary layer/ no worries


arcpy.CheckOutExtension("Network")
# arcpy.BuildNetwork_na(B1_ND)  # because the Rail2_ND file may have been changed
print("Network Rebuilt")
arcpy.MakeRouteLayer_na(B1_ND, "Route", "Length")



# creates a dictionary of two columns
def get_dictionary(columnA, columnB, dataframe_name):
    dict = {}
    for i in range(len(old_links)):
        dict[dataframe_name[columnA][i]] = []
        dict[dataframe_name[columnB][i]] = []
    for i in range(len(dataframe_name)):
        dict[dataframe_name[columnA][i]].append(dataframe_name[columnB][i])
        dict[dataframe_name[columnB][i]].append(dataframe_name[columnA][i])
    return dict


# (nodeid, nodeLayer, columnName) = (nodeid, snapped_old_nodes + ".shp", "NEAR_DIST")
def get_cell_value(nodeid, nodeLayer, columnName):
    layer = Dbf5(nodeLayer.split('.shp')[0] + '.dbf').to_dataframe().set_index('id')
    return layer[columnName][nodeid]


# nodeA and NodeB are integers

# (nodeAlayer, nodeBlayer, nodeAColumnName, nodeBColumnName, nodeA, nodeB) = (MyNodes, oldnodes, "Fid", "id", buffer_id, id)
def get_distance(nodeAlayer, nodeBlayer, nodeAColumnName, nodeBColumnName, nodeA, nodeB):
    # create a set of origin and destination FIPS to be loaded in the network analyst
    # print ("ArgGIS analyst: Job Received, ONODE: {0}, DNODE: {1} *".format(nodeA, nodeB)) # *these nodes are in different layers
    sys.stdout.write('.')
    arcpy.CheckOutExtension("Network")
    arcpy.Select_analysis(nodeAlayer, o, '{0} = {1}'.format(nodeAColumnName, nodeA))
    arcpy.Select_analysis(nodeBlayer, d, '{0} = {1}'.format(nodeBColumnName, nodeB))
    arcpy.Merge_management([o, d], m)
    arcpy.AddLocations_na("Route", "Stops", m, "Name Name #", "5000 Kilometers", "", "B1 SHAPE;B1_ND_Junctions SHAPE",
                          "MATCH_TO_CLOSEST", "CLEAR", "NO_SNAP", "5 Meters", "INCLUDE", "B1 #;B1_ND_Junctions #")
    try:
        arcpy.Solve_na("Route", "SKIP", "TERMINATE", "500 Kilometers")
        arcpy.SelectData_management("Route", "Routes")
        arcpy.FeatureToLine_management("Route\\Routes", feature, "", "ATTRIBUTES")
    except:
        return 999999
    return ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH')][0])


# (nodeid, nodeLayer, columnName)=(1538, newnodes, "Fid")
def get_buffer_nodes_ids(nodeid, nodeLayer, columnName):
    local_buffer_dist = buffer_dist
    if near_node_dict[nodeid][1] < local_buffer_dist:
        local_buffer_dist = near_node_dict[nodeid][1]
        print("Buffer Distance changed to {0} Miles".format(local_buffer_dist))
    if local_buffer_dist == 0:
        local_buffer_dist = 0.1  # minimum value for buffer distance
    # create a circular buffer of given miles
    arcpy.Select_analysis(snapped_old_nodes, temp, '{0} = {1}'.format(columnName, nodeid))
    arcpy.Buffer_analysis(temp, temp1, "{0} Miles".format(local_buffer_dist), "FULL", "ROUND", "NONE", "", "PLANAR")
    # find nodes around that buffer
    arcpy.MakeFeatureLayer_management(nodeLayer, 'feature_lyr')
    arcpy.SelectLayerByLocation_management('feature_lyr', "WITHIN", temp1, "", "NEW_SELECTION", "NOT_INVERT")
    list_of_ids = [row.getValue("Fid") for row in arcpy.SearchCursor('feature_lyr')]
    return list_of_ids


def get_all_ids(layerName):
    layer = Dbf5(layerName.split('.shp')[0] + '.dbf').to_dataframe()
    return list(set(list(layer['TARGET_Fid'])))


def get_near_node_dict(nodelayer):
    arcpy.Project_management(nodelayer, temp1, arcpy.SpatialReference(102039))
    arcpy.Near_analysis(temp1, temp1)
    near_node_dict = {row.getValue("Fid"): [row.getValue("NEAR_Fid"), row.getValue("NEAR_DIST") / 1609.34] for row in
                      arcpy.SearchCursor(temp1)}
    return near_node_dict


# if the node is too far from the network, no route is found, to solve this, all the nodes were first snapped to the nearest new link
def snap_old_nodes_to_nearest_new_link():
    print ("Snapping old_nodes to nearest new_links")
    arcpy.CopyFeatures_management(oldnodes, snapped_old_nodes)
    arcpy.Snap_edit(snapped_old_nodes, [[newlinks, "VERTEX", near_snap_dist]])




def get_id_of_connecting_oldnode(nodeid):
    connecting_list = [x for x in old_node_connections_dict if nodeid in x]
    flattened_list = [x for sublist in connecting_list for x in sublist]
    after_removing_nodeid_list = [x for x in flattened_list if x not in [nodeid]]
    return after_removing_nodeid_list




#links = newlinks
def get_old_node_connections_dict(links):

arcpy.FeatureVerticesToPoints_management(links, temp1, "BOTH_ENDS")
arcpy.SpatialJoin_analysis(temp1, oldnodes, temp2, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST")
nearfid_to_fips_fid = {row.getValue("FID"): [row.getValue("NEAR_FID"), row.getValue("ID_1")] for row in arcpy.SearchCursor(temp1)}
df = pandas.DataFrame(nearfid_to_fips_fid).transpose()
list_of_connected_nodes = []
for value in list(set(df[0].values)):
    list_of_connected_nodes.append(list(df[df[0] == value][1]))
return list_of_connected_nodes



def cut_new_to_old(newlinks, oldlinks):
    arcpy.Buffer_analysis(oldlinks,"in_memory/buffer", str(network_buffer_dist) + " Miles")
    arcpy.Dissolve_management("in_memory/buffer",temp)
    arcpy.SelectLayerByLocation_management(newlinks,"COMPLETELY_WITHIN", "in_memory/buffer2")
    arcpy.CopyFeatures_management(newlinks,temp)


# get the dict of all near nodes and their distance (used for smaller distances to modify local buffer distance)
near_node_dict = get_near_node_dict(oldnodes)

# this is the dictionary that connects oldnodes and new nodes
old_new_node_dictionary = {}

# dictionary of all connections between each node (in old network)
old_node_connections_dict = get_old_node_connections_dict(oldlinks)

# the program begins here

for row in arcpy.da.SearchCursor(oldnodes, ["FID"]):
    print "Old Node id: {0}".format(row[0])
    ids_distance_dict = {}
    buffer_ids = get_buffer_nodes_ids(row[0], newnodes, "FID")
    if len(buffer_ids) in [0, 1]:  # if no or 1 node nearby (no need to run)
        if len(buffer_ids) == 0:
            old_new_node_dictionary[row[0]] = ""
        else:  # if one node found
            old_new_node_dictionary[row[0]] = buffer_ids[0]
            buffer_ids = []  # empty for not letting the subsequent for loops run
            ids_distance_dict = {}  # empty
    ids_of_connecting_nodes = get_id_of_connecting_oldnode(row[0])
    print("\tIDs of connecting nodes: {0}".format(ids_of_connecting_nodes))

    for buffer_id in buffer_ids:
        print ("\tworking on buffer ID: {0}".format(buffer_id))
        ids_distance_dict[buffer_id] = 0
        dist = 0
        for id in ids_of_connecting_nodes:  # if route not found, find route in the new layer with the new nodes
            currdist = get_distance(newnodes, oldnodes, "FID", "FID", buffer_id, id)
            if currdist == 999999:
                print("\t\tRoute: New: {0}, Old: {1} not found".format(buffer_id,id))
                print("\t\tUsing Snapped Old Nodes..")
                currdist = get_distance(snapped_old_nodes, oldnodes, "FID", "FID", buffer_id, id)
                if currdist == 999999:
                    print("\t\t\tRoute not found, using Distance = 999999")
            dist += currdist
        ids_distance_dict[buffer_id] = dist
    # choosing the one with minimum distance
    for key, values in ids_distance_dict.iteritems():  # print id and distance formatted
        print ("\t\t{0}: {1}".format(key, values))
    # print ("{0}".format(ids_distance_dict))
    for key, values in ids_distance_dict.iteritems():
        if values == min(ids_distance_dict.values()):
            if values != max(
                    ids_distance_dict.values()):  # if min = max, the change of position of the node does not reduce the overall distance (hence left unchanged)
                old_new_node_dictionary[row[0]] = key
            else:
                old_new_node_dictionary[row[0]] = ""  # if max == min, just do nothing
    print ("Added to snap dictionary: {0}:{1}".format(row[0],old_new_node_dictionary[row[0]]))  # can be empty value

print("Node Conversion complete")


# for row in arcpy.da.SearchCursor(oldnodes, ["FID"]):
#     print "Old Node id: {0}".format(row[0])
#     ids_distance_dict = {}
#     buffer_ids = get_buffer_nodes_ids(row[0], newnodes, "FID")
#     if len(buffer_ids) in [0, 1]:  # if no or 1 node nearby (no need to run)
#         if len(buffer_ids) == 0:
#             old_new_node_dictionary[row[0]] = ""
#         else:  # if one node found
#             old_new_node_dictionary[row[0]] = buffer_ids[0]
#             buffer_ids = []  # empty for not letting the subsequent for loops run
#             ids_distance_dict = {}  # empty
#     ids_of_connecting_nodes = get_id_of_connecting_oldnode(row[0])
#     print("\tIDs of connecting nodes: {0}".format(ids_of_connecting_nodes))
#
#     for buffer_id in buffer_ids:
#         print ("\tworking on buffer ID: {0}".format(buffer_id))
#         ids_distance_dict[buffer_id] = 0
#         dist = 0
#         for id in ids_of_connecting_nodes:  # if route not found, find route in the new layer with the new nodes
#             currdist = get_distance(newnodes, oldnodes, "FID", "FID", buffer_id, id)
#             if currdist == 999999:
#                 print("\t\tRoute: New: {0}, Old: {1} not found".format(buffer_id,id))
#                 print("\t\tUsing Snapped Old Nodes..")
#                 currdist = get_distance(snapped_old_nodes, oldnodes, "FID", "FID", buffer_id, id)
#                 if currdist == 999999:
#                     print("\t\t\tRoute not found, using Distance = 999999")
#             dist += currdist
#         ids_distance_dict[buffer_id] = dist
#     # choosing the one with minimum distance
#     for key, values in ids_distance_dict.iteritems():  # print id and distance formatted
#         print ("\t\t{0}: {1}".format(key, values))
#     # print ("{0}".format(ids_distance_dict))
#     for key, values in ids_distance_dict.iteritems():
#         if values == min(ids_distance_dict.values()):
#             if values != max(
#                     ids_distance_dict.values()):  # if min = max, the change of position of the node does not reduce the overall distance (hence left unchanged)
#                 old_new_node_dictionary[row[0]] = key
#             else:
#                 old_new_node_dictionary[row[0]] = ""  # if max == min, just do nothing
#     print ("Added to snap dictionary: {0}:{1}".format(row[0],old_new_node_dictionary[row[0]]))  # can be empty value
#
# print("Node Conversion complete")
