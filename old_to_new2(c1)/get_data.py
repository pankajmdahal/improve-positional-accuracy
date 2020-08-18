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

sr_p = arcpy.SpatialReference(102039)
sr_g = arcpy.SpatialReference(4326)


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


def get_isolated_ids(node, link):
    arcpy.MakeFeatureLayer_management(node, "snapped")
    arcpy.SelectLayerByLocation_management("snapped", "INTERSECT", link, "", "NEW_SELECTION", "INVERT")
    return [f[0] for f in arcpy.da.SearchCursor("snapped", '_ID_')]


# how far is the nearest node (old network)
def get_near_node_dict(nodelayer):
    arcpy.Project_management(nodelayer, temp1, sr_p)
    fid_id_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(temp1)}
    arcpy.Near_analysis(temp1, temp1)
    near_node_dict = {row.getValue("_ID_"): [row.getValue("NEAR_Fid"), row.getValue("NEAR_DIST") / 1609.34] for row in
                      arcpy.SearchCursor(temp1)}
    near_node_dict = {x: [fid_id_dict[y[0]], y[1]] for x, y in near_node_dict.iteritems()}
    return near_node_dict

# to find out the old nodes within any distance *less than 5 miles here* of buffer nodes
def get_buffer_nodes_dist_dict():
    near_table = "in_memory//t1"
    arcpy.Project_management(new_n, temp1, sr_p)
    arcpy.GenerateNearTable_analysis(temp1, old_n, near_table, "6 Miles", "NO_LOCATION", "NO_ANGLE", "ALL", "10",
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


# find out the buffer nodes from current nodes at a distance mentioned
def get_currnode_buffernode_dist_dict():
    near_table = "in_memory//t1"
    arcpy.Project_management(old_n, temp1, sr_p)
    arcpy.GenerateNearTable_analysis(temp1, new_n, near_table, "7 Miles", "NO_LOCATION", "NO_ANGLE", "ALL", "100",
                                     "PLANAR")
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(near_table, ['IN_FID', 'NEAR_FID', 'NEAR_DIST']))
    new_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(new_n)}
    old_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(old_n)}
    df['IN_FID'] = df['IN_FID'].map(old_fid_ids_dict)
    df['NEAR_FID'] = df['NEAR_FID'].map(new_fid_ids_dict)
    df_dict = df.transpose().to_dict()
    ids_nearids_dict = {}
    for key, values in df_dict.iteritems():
        if values['IN_FID'] in ids_nearids_dict:
            ids_nearids_dict[values['IN_FID']][values["NEAR_FID"]] = values["NEAR_DIST"] / 1609.04
        else:
            ids_nearids_dict[values['IN_FID']] = {values['NEAR_FID']: values["NEAR_DIST"] / 1609.04}
    return ids_nearids_dict


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


def get_coordinates(link, id):
    new_dict = {}
    with arcpy.da.SearchCursor(link, [id, "SHAPE@XY"]) as curs:
        for _id_, xy in curs:
            new_dict[_id_] = xy
    return new_dict


def get_nearest_ground_truth_dict():
    near_table = "in_memory//t1"
    memory_ngt = "in_memory//ngt1"
    arcpy.CopyFeatures_management(new_ngt, memory_ngt)
    arcpy.Near_analysis(memory_ngt, new_n)
    nearfid_to_ground_id = {row.getValue("ID"): row.getValue("NEAR_FID") for row in arcpy.SearchCursor(memory_ngt)}
    new_fid_ids_dict = {row.getValue("FID"): row.getValue("_ID_") for row in arcpy.SearchCursor(new_n)}
    nearfid_to_ground_id = {x: new_fid_ids_dict[y] for x, y in nearfid_to_ground_id.iteritems()}
    arcpy.Project_management(new_n, temp1, sr_p)
    arcpy.GenerateNearTable_analysis(temp1, new_ngt, near_table, "10 Miles", "NO_LOCATION", "NO_ANGLE", "ALL", "10",
                                     "PLANAR")
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(near_table, ['IN_FID', 'NEAR_FID', 'NEAR_DIST']))
    newn_fid_ids_dict = {row.getValue("FID"): row.getValue("ID") for row in arcpy.SearchCursor(new_ngt)}
    df['IN_FID'] = df['IN_FID'].map(new_fid_ids_dict)
    df['NEAR_FID'] = df['NEAR_FID'].map(newn_fid_ids_dict).map(nearfid_to_ground_id)
    df['NEAR_DIST'] = df['NEAR_DIST'] / 1609.04
    # df.dropna(inplace=True)
    ids_nearids_dict = {}
    for i in range(len(df)):
        if df.IN_FID[i] in ids_nearids_dict:
            ids_nearids_dict[df.IN_FID[i]][df.NEAR_FID[i]] = df.NEAR_DIST[i]
        else:
            ids_nearids_dict[df.IN_FID[i]] = {df.NEAR_FID[i]: df.NEAR_DIST[i]}
    return ids_nearids_dict


#get value live
# get the dict of all near nodes and their distance (used for smaller distances to modify local buffer distance)
isolated_ids = get_isolated_ids(old_ns, new_l)
near_node_dict = get_near_node_dict(old_n)
ids_nearids_dist_dict = get_buffer_nodes_dist_dict()
curnod_buffnod_dist_dict = get_currnode_buffernode_dist_dict()
old_node_connections_dict = get_old_node_connections_dict(old_l) # dictionary of all connections between each node (in old network)
new_node_id_coordinates_dict = get_coordinates(new_n, "_ID_")
old_node_id_coordinates_dict = get_coordinates(old_ns, "_ID_")
nearest_ground_truth_dict = get_nearest_ground_truth_dict()


np.save('./intermediate/isolated_ids', np.array((isolated_ids)))
np.save('./intermediate/near_node_dict', np.array((near_node_dict)))
np.save('./intermediate/ids_nearids_dist_dict', np.array((ids_nearids_dist_dict)))
np.save('./intermediate/curnod_buffnod_dist_dict', np.array((curnod_buffnod_dist_dict)))
np.save('./intermediate/old_node_connections_dict', np.array((old_node_connections_dict)))
np.save('./intermediate/new_node_id_coordinates_dict', np.array((new_node_id_coordinates_dict)))
np.save('./intermediate/old_node_id_coordinates_dict', np.array((old_node_id_coordinates_dict)))
np.save('./intermediate/nearest_ground_truth_dict', np.array((nearest_ground_truth_dict)))