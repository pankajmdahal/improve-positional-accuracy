# work on IDs not FIDs, IDs never change, FIDs do
import pandas
import arcpy
from parameters import *
import random
import numpy as np

m = "in_memory/m11"

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

arcpy.env.overwriteOutput = True  # overwrite files if its already present
arcpy.CheckOutExtension("Network")
arcpy.BuildNetwork_na(B1_ND)
arcpy.MakeRouteLayer_na(B1_ND, B1_route, "Length")
arcpy.MakeFeatureLayer_management(new_l, "newlf")


# how far is the nearest node (old network)
def get_near_node_dict(nodelayer):
    arcpy.Project_management(nodelayer, temp1, arcpy.SpatialReference(102039))
    fid_id_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(temp1)}
    arcpy.Near_analysis(temp1, temp1)
    near_node_dict = {row.getValue("_ID_"): [row.getValue("NEAR_Fid"), row.getValue("NEAR_DIST") / 1609.34] for row in
                      arcpy.SearchCursor(temp1)}
    near_node_dict = {x: [fid_id_dict[y[0]], y[1]] for x, y in near_node_dict.iteritems()}
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
    return ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH')][0])



def get_dist(points,current_id,buffer_id):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(arcpy.SpatialReference(4326))
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
    return _list_, ([f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH')][0])




#creates links in GIS and returns linkIDs
def get_distance1(ids_of_connecting_nodes,current_id, buffer_id):
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
        return dist,0
    if max_count ==1: ##only append the proper ones (the size of the shapefile is limited)
        no_overlapping_found_flag = 1
        try:
           arcpy.Append_management(feature, empty_memory)
        except: #if its the first time
            arcpy.CopyFeatures_management(feature, empty_memory)
    return dist,no_overlapping_found_flag




#to find out the old nodes within any distance *less than 5 miles here* of buffer nodes
def get_buffer_nodes_dist_dict():
    near_table = "in_memory//t1"
    arcpy.Project_management(new_n, temp1, arcpy.SpatialReference(102039))
    arcpy.GenerateNearTable_analysis(temp1, old_n, near_table, "5 Miles", "NO_LOCATION", "NO_ANGLE", "ALL", "3",
                                     "PLANAR")
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(near_table, ['IN_FID', 'NEAR_FID', 'NEAR_DIST']))
    new_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(new_n)}
    old_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(old_n)}
    df['IN_FID'] = df['IN_FID'].map(new_fid_ids_dict)
    df['NEAR_FID'] = df['NEAR_FID'].map(old_fid_ids_dict)
    df_dict = df.transpose().to_dict()
    ids_nearids_dict = {}
    for key, value in df_dict.iteritems():
        ids_nearids_dict.setdefault(value['NEAR_FID'], []).append([value['IN_FID'], value['NEAR_DIST'] / 1609.04])
    return ids_nearids_dict

#find out the buffer nodes from current nodes at a distance mentioned
def get_currnode_buffernode_dist_dict():
    near_table = "in_memory//t1"
    arcpy.Project_management(old_n, temp1, arcpy.SpatialReference(102039))
    arcpy.GenerateNearTable_analysis(temp1, new_n, near_table, "6 Miles", "NO_LOCATION", "NO_ANGLE", "ALL", "100","PLANAR")
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(near_table, ['IN_FID', 'NEAR_FID', 'NEAR_DIST']))
    new_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(new_n)}
    old_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(old_n)}
    df['IN_FID'] = df['IN_FID'].map(old_fid_ids_dict)
    df['NEAR_FID'] = df['NEAR_FID'].map(new_fid_ids_dict)
    df_dict = df.transpose().to_dict()
    ids_nearids_dict = {}
    for key,values in df_dict.iteritems():
        if values['IN_FID'] in ids_nearids_dict:
            ids_nearids_dict[values['IN_FID']][values["NEAR_FID"]] = values["NEAR_DIST"]/1609.04
        else:
            ids_nearids_dict[values['IN_FID']] = {values['NEAR_FID']:values["NEAR_DIST"]/1609.04}
    return ids_nearids_dict



# (ID, nodeLayer, columnName)=(1538, new_n, "Fid")
def get_buffer_nodes_ids(ID):
    local_buffer_dist = buffer_dist
    # the buffer distance cannot be more than the distance to nearest node
    if near_node_dict[ID][1] < local_buffer_dist:
        local_buffer_dist = near_node_dict[ID][1]  # in some cases its better to go beyond
        print("Buffer Distance changed to {0} Miles".format(local_buffer_dist))
    # create a circular buffer of given miles
    list_of_ids = [x for [x, y] in ids_nearids_dist_dict[ID] if y < local_buffer_dist]
    return list_of_ids


# links = old_links_shp
def get_old_node_connections_dict(links):
    arcpy.FeatureVerticesToPoints_management(links, temp1, "BOTH_ENDS")
    arcpy.SpatialJoin_analysis(temp1, old_n, temp2, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST")
    nearfid_to_fips_fid = [[row.getValue("ORIG_FID"), row.getValue("_ID1")] for row in arcpy.SearchCursor(temp2)]
    a = {}
    for linkid, nodeid in nearfid_to_fips_fid:
        a.setdefault(linkid, []).append(nodeid)
    b = a.values()
    node_node_dict = {}
    for list in b:
        try:
            node1, node2 = list
        except:
            print ("multipart on oldnodeIDs {0}".format(list))
        node_node_dict.setdefault(node1, []).append(node2)
        node_node_dict.setdefault(node2, []).append(node1)
    return node_node_dict


# links = old_links_shp
def get_new_link_connections_dict(links):
    arcpy.FeatureVerticesToPoints_management(new_l, memory_1, "BOTH_ENDS")
    arcpy.SpatialJoin_analysis(memory_1, new_n, memory_2, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST")
    nearfid_to_fips_fid = [[row.getValue("ORIG_FID"), row.getValue("_ID1")] for row in arcpy.SearchCursor(memory_2)]
    a = {}
    for linkid, nodeid in nearfid_to_fips_fid:
        a.setdefault(nodeid, []).append(linkid)
    b = {}
    for linkid, nodeid in nearfid_to_fips_fid:
        b.setdefault(linkid, []).append(nodeid)
    c = {}
    for key, value in b.iteritems():
        c[key] = [a[x] for x in b]


def get_coordinates(link, id):
    new_dict = {}
    with arcpy.da.SearchCursor(link, [id, "SHAPE@XY"]) as curs:
        for _id_, xy in curs:
            new_dict[_id_] = xy
    return new_dict


def get_nearest_ground_truth_dict():
    arcpy.Near_analysis(new_n, new_ngt)
    near_dist_dict = {f[0]: f[1] for f in arcpy.da.SearchCursor(new_n, ['_ID_', "NEAR_DIST"])}
    return near_dist_dict


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]






# find the nodes that are not connected to anyone (aka. did not find any snaps in the new network, could be skipped later)
arcpy.MakeFeatureLayer_management(old_ns, "snapped")
arcpy.SelectLayerByLocation_management("snapped", "INTERSECT", new_l, "", "NEW_SELECTION", "INVERT")
isolated_ids = [f[0] for f in arcpy.da.SearchCursor("snapped", '_ID_')]

# get the dict of all near nodes and their distance (used for smaller distances to modify local buffer distance)
near_node_dict = get_near_node_dict(old_n)
ids_nearids_dist_dict = get_buffer_nodes_dist_dict()
curnod_buffnod_dist_dict = get_currnode_buffernode_dist_dict()



# dictionary of all connections between each node (in old network)
old_node_connections_dict = get_old_node_connections_dict(old_l)

# the program begins here
new_node_id_coordinates_dict = get_coordinates(new_n, "_ID_")
old_node_id_coordinates_dict = get_coordinates(old_ns, "_ID_")

nearest_ground_truth_dict = get_nearest_ground_truth_dict()

# for randomness
connections_gt3_list = [x for x, y in old_node_connections_dict.iteritems() if len(y) > 2]

# existing file
try:
    all_dict = np.load('all_dict.npy')
except:
    all_dict = {}

try:
    all_ids_dist_dict = np.load('all_ids_dist_dict.npy')
except:
    all_ids_dist_dict = {}



route_not_found_dict = {}
multiple_minimum = {}

buffer_dists = [float(x) / 10 for x in range(30, 0, -1)]  # [3,2.9,....0.1]
sample_size = 30
curr_ids = random.sample(connections_gt3_list, sample_size)
curr_ids = connections_gt3_list



for current_id in curr_ids:
    bufferdist_snappednode_dict = {}  # has all buffer distance and snapped node
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
    ids_of_connecting_nodes = list(set([x for x in ids_of_connecting_nodes if x not in isolated_ids]))
    print("\tIDs of connecting nodes: {0}".format(ids_of_connecting_nodes))  # in old network
    # remove the buffer_node_ids that are not in the snapped_removed_ids
    # buffer_node_ids
    count = 0
    for buffer_id,distance in sorted_buffer_nodes:
        if distance > near_node_dict[current_id][1]*2: #cannot be too close
            break
        if buffer_id in ids_distance_dict:
            print ("sum of paths known for bufferid: {0}".format(buffer_id))
            continue
        else: #id not present (check if further going necessary
            ids_distance_dict[buffer_id]


        dist1,overlap_flag = get_distance1(ids_of_connecting_nodes, current_id, buffer_id)
        ids_distance_dict[buffer_id] = dist1,overlap_flag
        if overlap_flag ==1:
            count = 100000
        count = count+1
    all_ids_dist_dict[current_id] = ids_distance_dict
    # save dictionaries as numpy objects
    np.save('all_ids_dist_dict1', np.array(dict(all_ids_dist_dict)))
    np.save('all_dict1', np.array(dict(all_dict)))


import numpy as np
import pandas as pd


try:
    all_dict = np.load('all_dict1.npy').item()
except:
    all_dict = {}

try:
    all_ids_dist_dict = np.load('all_ids_dist_dict1.npy').item()
except:
    all_ids_dist_dict = {}



def get_test(dist, val):
    if dist<threshold:
        if val > 0:
            return val
    else:
        return 0


all_unoverlapped = {}
for x, y in all_ids_dist_dict.iteritems():
    all_unoverlapped[x] = [p for p, q in y.iteritems() if q[1] == 1]
    #if none found with no overlapped
    if len(all_unoverlapped[x])==0:
        all_unoverlapped[x] = [p for p, q in y.iteritems()]
    _min_ = min([q[0] for p, q in y.iteritems()])
    all_unoverlapped[x] = [p for p, q in y.iteritems() if q[0]==_min_][0]


data_df = pd.DataFrame.from_dict(all_unoverlapped, orient='index')
#data_df.to_csv("buffer_node_dist.csv")
threshold = 0.01
data_df[1] = data_df[0].map(nearest_ground_truth_dict)
data_df[2] = np.where((data_df[1] <= threshold) , 1, 0)

accuracy = data_df.mean()[2]



#plotting
plot_interesting = {}
_dumm_ = {}
for x, y in all_ids_dist_dict.iteritems():
    for p,q in y.iteritems():
        _dist_ = [m for l,m in curnod_buffnod_dist_dict[x].iteritems() if p== l][0]
        _dumm_[p] = [q[0], nearest_ground_truth_dict[p], _dist_,q[1]]
    plot_interesting[x] = _dumm_
    _dumm_ = {}




np.save('plot_dict11', np.array(dict(plot_interesting)))

















del plot_dict['test']
np.save('plot_dict', np.array(dict(plot_dict)))
pandas.DataFrame.from_dict(plot_dict, orient= 'index').transpose().to_csv("plot4.csv")

data_df1.to_csv("appppple.csv")


unique_values = pandas.unique(data_df[buffer_dists].values.ravel())
list_of_found_nodes = [x for x in unique_values if x not in [-99, -98, -97, -96, -95]]

arcpy.MakeFeatureLayer_management(new_n, "newnf")
arcpy.SelectLayerByAttribute_management("newnf", "NEW_SELECTION", get_where_clause("_ID_", list_of_found_nodes))
arcpy.CopyFeatures_management("newnf", temp)
arcpy.Near_analysis(temp, new_ngt)

print("Node Conversion complete")







def get_buffer_node_ids1(curr):
    all = all_dict[curr].values()
    return set([x for x in all if x not in [-99, -98, -97, -96, -95]])


arcpy.DeleteFeatures_management(empty_memory)

count_link_dict = {}
for current_id in curr_ids:

print("Old Node ID: {0}".format(current_id))
ids_of_connecting_nodes = old_node_connections_dict[current_id]
buffer_dist = 3
buffer_node_ids = get_buffer_node_ids1(current_id)
buffer_node_ids = [x for x in buffer_node_ids if x in list_of_found_nodes]
print (buffer_node_ids)
count_link_from_currentid_dict = {}
for buffer_id in buffer_node_ids:
    count_dict = {}
    for id in ids_of_connecting_nodes:
        pair = new_node_id_coordinates_dict[buffer_id], old_node_id_coordinates_dict[id]
        list_of_links = get_distance1(pair,current_id, buffer_id)

    count_link_from_currentid_dict[buffer_id] = count_dict



count_link_dict[current_id] = count_link_from_currentid_dict


arcpy.CopyFeatures_management(empty_memory, temp1)
arcpy.Dissolve_management(temp1, temp2, ['curr_id', 'buffer_id'], [["Total_leng", "SUM"]], "MULTI_PART", "DISSOLVE_LINES")


_range_ = [float(x)/10 for x in reversed(range(5,15,1))]
data_df2 = data_df.copy()
threshold = 0.01
buffer_dists2 = [x for x in buffer_dists if x in _range_]
data_df2 = data_df2[buffer_dists2]
for colname in buffer_dists2:
    data_df2[colname] = data_df2[colname].map(nearest_ground_truth_dict)

data_df2['test']= data_df2[buffer_dists2].min(axis=1)

for colname in buffer_dists2:
    data_df2[colname] = np.where((data_df2[colname] == data_df2['test']) , 1, 0)

plot_dict = data_df2.sum().to_dict()
del plot_dict['test']
np.save('plot_dict', np.array(dict(plot_dict)))
pandas.DataFrame.from_dict(plot_dict, orient= 'index').transpose().to_csv("plot2.csv")

data_df2.to_csv("aaaa.csv")