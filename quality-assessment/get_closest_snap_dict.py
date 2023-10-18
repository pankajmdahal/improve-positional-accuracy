# finding links that are not in the base network

import arcpy
import sys
import csv
import pandas as pd
import os
from merge import *

arcpy.env.overwriteOutput = True

other = "./intermediate/NARN_LINE_03162018.shp"
base = "./intermediate/railway_ln_connected.shp"

arcpy.CheckOutExtension("Network")

start_end_ids_dict = {row1.getValue("_ID_"): [row1.getValue("_A_"), row1.getValue("_B_"), row1.getValue("_LEN_")]
                      for row1 in arcpy.SearchCursor(base)}


def get_touching_ids(link_id):  # doesnot returns itself
    start_end_id = start_end_ids_dict[link_id]
    touching_ids = [key for key, value in start_end_ids_dict.iteritems() if
                    value[0] in start_end_id or value[1] in start_end_id]
    touching_ids.remove(link_id)
    return touching_ids


def remove_touching_linkids(list):
    print "Original List {0}".format(list)
    touching_ids = get_touching_ids(list[0])  # use this as base to remove all ids touching this
    return [x for x in list if x not in touching_ids]


def get_all_nodes_in_link(link):
    nodes_inside_ = []
    link_node_dict = {row2.getValue("_ID_"): [row2.getValue("_A_"), row2.getValue("_B_")] for row2 in
                      arcpy.SearchCursor(link)}
    for key, value in link_node_dict.iteritems():
        if value[0] not in nodes_inside_:
            nodes_inside_.append(value[0])
        if value[1] not in nodes_inside_:
            nodes_inside_.append(value[1])
        continue
    return nodes_inside_


def add_row(input, number):
    for row in arcpy.SearchCursor(input):
        shp = row.getValue("SHAPE")
    #
    for i in range(number):
        feat = arcpy.InsertCursor(input).newRow()
        feat.shape = shp
        arcpy.InsertCursor(input).insertRow(feat)


def get_coordinates_on_nearest_links(node_shp, link_shp_f, link_ids): #they have same number of features
    nearxy = []
    count = len(link_ids)
    add_row(node_shp, count - 1)
    for i in range(count):
        where_clause = """ "_ID_" = %d""" % link_ids[i]
        arcpy.SelectLayerByAttribute_management(link_shp_f, "NEW_SELECTION", where_clause)
        arcpy.SelectLayerByAttribute_management("mf", "NEW_SELECTION", "FID IN ({})".format(i))
        arcpy.Snap_edit("mf", [[base_f, "EDGE", buffer_dist_list[-1]]])  # the  max snap distance is taken from there
    #
    with arcpy.da.SearchCursor(m1, ["SHAPE@XY"]) as curs:
        for xy in curs:
            nearxy.append(xy[0])
    #
    return nearxy


node_id_to_link_ids_df = pd.read_csv("id_min_dist.csv")
node_id_to_link_ids_dict = node_id_to_link_ids_df.transpose().to_dict()
node_id_to_link_ids_dict = {y['IDs: ']: eval(y['IDs of Links']) for x, y in node_id_to_link_ids_dict.iteritems()}


# clipping the shapefile and getting node-coordinate dict
nodes_inside = get_all_nodes_in_link(other)
#each link is associated with 2 nodes, make its dictionary
other_pt = other
other_pt = other_pt.replace("intermediate/", "intermediate/pt_")
arcpy.MakeFeatureLayer_management(base, base_f)
arcpy.MakeFeatureLayer_management(other_pt, other_pt_f)
# find the nearest coordinates to those links
near_ids = {}
no_nearby_linkids = []
id_buffer_dict = {}
arcpy.AddSpatialIndex_management(base_f)  # adjusted comment from gis.stackoverflow, why?
for key in nodes_inside:
    print key
    where_clause = """ "_ID_" = %d""" % key
    arcpy.SelectLayerByAttribute_management(other_pt_f, "NEW_SELECTION", where_clause)
    ids_list = node_id_to_link_ids_dict[key]
    print ids_list

    if len(ids_list) == 0:
        print ("X: {0}".format(key)) #highest range did not work
        no_nearby_linkids.append(key)
        continue
    #
    print "Proximite link IDs: {1}".format(len(ids_list), ids_list)
    arcpy.CopyFeatures_management(other_pt_f, m1) #only one row
    arcpy.MakeFeatureLayer_management(m1, "mf")
    near_ids[key] = get_coordinates_on_nearest_links(m1, base_f, ids_list)


pd.DataFrame({key: pd.Series(value) for key, value in near_ids.iteritems()}).transpose().to_csv(
    node_coordinates_dict)
pd.DataFrame(no_nearby_linkids).to_csv(no_nearby_dict)













