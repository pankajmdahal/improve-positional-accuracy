# work on IDs not FIDs, IDs never change, FIDs do
import pandas
import arcpy
from parameters import *
import random
import numpy as np
import os

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
reduced_shape = "C:/GIS/reduced_shape.shp"
reduced_nodes = "C:/GIS/reduced_nodes.shp"


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


def get_isolated_ids(nodes, link):
    # snap nodes to calculate routes
    arcpy.CopyFeatures_management(nodes, snapped_old_nodes)  # the old nodes are snapped to the new link, to calculate the sum distance
    arcpy.MakeFeatureLayer_management(snapped_old_nodes, "snapped")
    arcpy.Snap_edit(snapped_old_nodes, [[link, "EDGE", near_snap_dist]])
    arcpy.SelectLayerByLocation_management("snapped", "INTERSECT", link, "", "NEW_SELECTION", "INVERT")
    ids = [f[0] for f in arcpy.da.SearchCursor("snapped", '_ID_')]
    return {x: "" for x in ids}



# how far is the nearest node (old network)
def get_near_node_dict(nodelayer):
    arcpy.Project_management(nodelayer, temp1, sr_p)
    fid_id_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(temp1)}
    arcpy.Near_analysis(temp1, temp1)
    near_node_dict = {row.getValue("_ID_"): [row.getValue("NEAR_Fid"), row.getValue("NEAR_DIST") / 1609.34] for row in
                      arcpy.SearchCursor(temp1)}
    near_node_dict = {x: [fid_id_dict[y[0]], y[1]] for x, y in near_node_dict.iteritems()}
    return near_node_dict


# to find out the buffer_nodes within a specified distance of the old node
def get_buffer_nodes_dist_dict():
    near_table = "in_memory//t1"
    temp = "C:/GIS/temp.shp"
    arcpy.Project_management(new_n, temp, sr_p)  #
    arcpy.MakeFeatureLayer_management(temp, "new_n")  # do not select the dangling nodes
    arcpy.GenerateNearTable_analysis(temp, old_n, near_table, str(curr_node_buff_node_dist + 2) + " Miles",
                                     "NO_LOCATION", "NO_ANGLE", "ALL", "10",
                                     "PLANAR")
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(near_table, ['IN_FID', 'NEAR_FID', 'NEAR_DIST']))
    new_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(new_n)}
    old_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(old_n)}
    df['IN_FID'] = df['IN_FID'].map(new_fid_ids_dict)
    df['NEAR_FID'] = df['NEAR_FID'].map(old_fid_ids_dict)

    df = df[df.IN_FID.isin(potential_ids.keys())]

    df_dict = df.transpose().to_dict()
    ids_nearids_dict = {}
    for key, value in df_dict.iteritems():
        ids_nearids_dict.setdefault(value['NEAR_FID'], []).append([value['IN_FID'], value['NEAR_DIST'] / 1609.04])
        # ids_nearids_dict.setdefault(value['NEAR_FID'], []).append(value['IN_FID'])
    return ids_nearids_dict


# find out the buffer nodes from current nodes at a distance mentioned
def get_currnode_buffernode_dist_dict():
    near_table = "in_memory//t1"
    temp = "C:/GIS/temp.shp"
    arcpy.Project_management(old_n, temp1, sr_p)
    arcpy.MakeFeatureLayer_management(new_n, "new_n")
    # arcpy.SelectLayerByAttribute_management("new_n", "SWITCH_SELECTION", get_where_clause("_ID_", dangling_ids)) # the list was too big, python crashed
    arcpy.CopyFeatures_management("new_n", temp)
    arcpy.GenerateNearTable_analysis(temp1, temp, near_table, str(curr_node_buff_node_dist + 2) + " Miles",
                                     "NO_LOCATION", "NO_ANGLE", "ALL", "200",
                                     "PLANAR")
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(near_table, ['IN_FID', 'NEAR_FID', 'NEAR_DIST']))
    new_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(temp)}
    old_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(old_n)}
    df['IN_FID'] = df['IN_FID'].map(old_fid_ids_dict)
    df['NEAR_FID'] = df['NEAR_FID'].map(new_fid_ids_dict)
    # print df
    df = df[df.NEAR_FID.isin(potential_ids.keys())]
    df_dict = df.transpose().to_dict()
    ids_nearids_dict = {}
    for key, values in df_dict.iteritems():
        if values['IN_FID'] in ids_nearids_dict:
            ids_nearids_dict[values['IN_FID']][values["NEAR_FID"]] = values["NEAR_DIST"] / 1609.04
        else:
            ids_nearids_dict[values['IN_FID']] = {values['NEAR_FID']: values["NEAR_DIST"] / 1609.04}
    return ids_nearids_dict


# dictionary of all connections between each node (in old network)
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


def get_coordinates(link, id):
    new_dict = {}
    with arcpy.da.SearchCursor(link, [id, "SHAPE@XY"]) as curs:
        for _id_, xy in curs:
            new_dict[_id_] = xy
    return new_dict


#distance between any current node and some ground truth nodes
def get_nearest_ground_truth_dict():
    temp2 = "C:/gis/temp.shp"
    near_table = "in_memory//t2"
    memory_ngt = "in_memory//ngt1"
    #
    arcpy.CopyFeatures_management(new_ngt, memory_ngt) # since near analysis overwrites in the original shp
    arcpy.Near_analysis(memory_ngt, reduced_nodes) # do near analysis only to potential nodes
    #
    arcpy.Project_management(reduced_nodes, temp2, sr_p) #to find nodes around a distance
    #
    new_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(reduced_nodes)}
    newn_fid_ids_dict = {row.getValue("ID"): row.getValue("FID")  for row in arcpy.SearchCursor(memory_ngt)}
    # #
    nearfid_to_ground_id = {newn_fid_ids_dict[row.getValue("ID")]: new_fid_ids_dict[row.getValue("NEAR_FID")] for row in arcpy.SearchCursor(memory_ngt)}
    #
    arcpy.GenerateNearTable_analysis(temp2, memory_ngt, near_table, str(curr_node_buff_node_dist + 3) + " Miles",
                                     "NO_LOCATION", "NO_ANGLE", "ALL", "10",
                                     "PLANAR")
    #
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(near_table, ['IN_FID', 'NEAR_FID', 'NEAR_DIST']))
    #
    df['IN_FID'] = df['IN_FID'].map(new_fid_ids_dict)
    df['NEAR_FID'] = df['NEAR_FID'].map(nearfid_to_ground_id)
    df['NEAR_DIST'] = df['NEAR_DIST'] / 1609.04
    #
    df = df.loc[df.groupby(['IN_FID','NEAR_FID']).NEAR_DIST.idxmin()] #since some gt nodes donot have any reduced nodes nearby (snaps to wrong node)
    df = df.reset_index()[['IN_FID', 'NEAR_FID', 'NEAR_DIST']] #since 1^ removes some indexes
    #
    ids_nearids_dict = {}
    for i in range(len(df)):
        if df.IN_FID[i] in ids_nearids_dict:
            ids_nearids_dict[df.IN_FID[i]][df.NEAR_FID[i]] = df.NEAR_DIST[i]
        else:
            ids_nearids_dict[df.IN_FID[i]] = {df.NEAR_FID[i]: df.NEAR_DIST[i]}
    # ids_nearids_dict = {x:y for x,y in ids_nearids_dict.iteritems() if x in potential_ids.keys()}
    return ids_nearids_dict


def remove_all_dangling_links_from(link_shp):
    links_f = "linksf"
    temp = "in_memory/nodes"
    link_temp = "in_memory/links"
    arcpy.CopyFeatures_management(link_shp, link_temp)
    arcpy.MakeFeatureLayer_management(link_temp, links_f)
    while True:
        arcpy.FeatureVerticesToPoints_management(links_f, temp, "DANGLE")
        count_curr = len([_row_[0] for _row_ in arcpy.da.SearchCursor(temp, ['FID'])])
        print count_curr
        if count_curr <= 10:
            return links_f
        arcpy.SelectLayerByLocation_management(links_f, "INTERSECT", temp, "", "NEW_SELECTION", "")
        arcpy.DeleteFeatures_management(links_f)
        arcpy.CopyFeatures_management(link_temp, reduced_shape) # for calculation of isolated ids


def get_nodes_connected_to_at_least_3_links(node_shp, link_shp):
    nodes_f = "nodesf"
    temp1 = "in_memory/m1"
    temp2 = "in_memory/m2"
    temp3 = "in_memory/m3"
    links_f = "links_f"
    arcpy.MakeFeatureLayer_management(node_shp, nodes_f)
    arcpy.MakeFeatureLayer_management(link_shp, links_f)
    link_shp = remove_all_dangling_links_from(link_shp)
    arcpy.Dissolve_management(link_shp, temp3, "", "", "SINGLE_PART", "UNSPLIT_LINES")
    arcpy.FeatureToLine_management(temp3, temp1, "", "NO_ATTRIBUTES")
    arcpy.FeatureVerticesToPoints_management(temp1, temp2, "BOTH_ENDS")
    arcpy.SelectLayerByLocation_management(nodes_f, "INTERSECT", temp2, "", "NEW_SELECTION", "")
    arcpy.CopyFeatures_management(nodes_f, reduced_nodes)
    potential_ids = {row.getValue("_ID_"): "" for row in arcpy.SearchCursor(nodes_f)}
    return potential_ids



# get value live
# get the dict of all near nodes and their distance (used for smaller distances to modify local buffer distance)
isolated_ids = get_isolated_ids(old_n, reduced_shape)
potential_ids = get_nodes_connected_to_at_least_3_links(new_n, new_l)
near_node_dict = get_near_node_dict(old_n)
ids_nearids_dist_dict = get_buffer_nodes_dist_dict()  # distance from old_id
curnod_buffnod_dist_dict = get_currnode_buffernode_dist_dict()
old_node_connections_dict = get_old_node_connections_dict(old_l)
new_node_id_coordinates_dict = get_coordinates(new_n, "_ID_")
old_node_id_coordinates_dict = get_coordinates(old_ns, "_ID_")
nearest_ground_truth_dict = get_nearest_ground_truth_dict()


potential_ids = np.load('./intermediate/potential_ids.npy').item()

np.save('./intermediate/isolated_ids', np.array((isolated_ids)))
np.save('./intermediate/potential_ids', np.array((potential_ids)))
np.save('./intermediate/near_node_dict', np.array((near_node_dict)))
np.save('./intermediate/ids_nearids_dist_dict', np.array((ids_nearids_dist_dict)))
np.save('./intermediate/curnod_buffnod_dist_dict', np.array((curnod_buffnod_dist_dict)))
np.save('./intermediate/old_node_connections_dict', np.array((old_node_connections_dict)))
np.save('./intermediate/new_node_id_coordinates_dict', np.array((new_node_id_coordinates_dict)))
np.save('./intermediate/old_node_id_coordinates_dict', np.array((old_node_id_coordinates_dict)))
np.save('./intermediate/nearest_ground_truth_dict', np.array((nearest_ground_truth_dict)))
