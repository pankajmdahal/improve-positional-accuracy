# finding links that are not in the base network

import arcpy
import sys
import csv
import pandas as pd
import numpy as np
import os
from merge import *
import multiprocessing
from functools import partial


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


def get_coordinates_on_nearest_links(node_shp, link_shp, link_ids):  # they have same number of features
    link_shp_f = "link_shpf"
    arcpy.MakeFeatureLayer_management(node_shp, "mf")
    arcpy.MakeFeatureLayer_management(link_shp, link_shp_f)
    nearxy = []
    count = len(link_ids)
    add_row(node_shp, count - 1)
    for i in range(count):
        where_clause = """ "_ID_" = %d""" % link_ids[i]
        arcpy.SelectLayerByAttribute_management(link_shp_f, "NEW_SELECTION", where_clause)
        arcpy.SelectLayerByAttribute_management("mf", "NEW_SELECTION", "FID IN ({})".format(i))
        arcpy.Snap_edit("mf", [[link_shp_f, "EDGE", buffer_dist_list[-1]]])  # the  max snap distance is taken from there
    #
    with arcpy.da.SearchCursor(m1, ["SHAPE@XY"]) as curs:
        for xy in curs:
            nearxy.append(xy[0])
    #
    return nearxy


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


def get_distance_blabla(node_id_to_link_ids_dict, base, other_pt,
                        start_end_ids_dict, key):
    arcpy.env.overwriteOutput = True
    m1 = "in_memory/m1"
    other_pt_f = "opf"
    arcpy.MakeFeatureLayer_management(other_pt, other_pt_f)
    ids_list = node_id_to_link_ids_dict[key]
    if len(ids_list) == 0:
        return (np.nan, np.nan)
    print "Node: {0}, Proximite link IDs: {1}".format(key, ids_list)
    where_clause = """ "_ID_" = %d""" % key
    #print where_clause
    arcpy.SelectLayerByAttribute_management(other_pt_f, "NEW_SELECTION", where_clause)
    arcpy.CopyFeatures_management(other_pt_f, m1)  # only one row
    return get_coordinates_on_nearest_links(m1, base, ids_list)


def get_near_id_to_link_ids_dict(csv_name):
    node_id_to_link_ids_df = pd.read_csv(csv_name)
    node_id_to_link_ids_dict = node_id_to_link_ids_df.transpose().to_dict()
    node_id_to_link_ids_dict = {int(y['IDs: ']): eval(y['IDs of Links']) for x, y in node_id_to_link_ids_dict.iteritems()}
    return node_id_to_link_ids_dict


def main():
    # arcpy.AddSpatialIndex_management(base_f)  # adjusted comment from gis.stackoverflow, why?
    arcpy.env.overwriteOutput = True
    other = "./intermediate/NARN_LINE_03162018.shp"
    base = "./intermediate/railway_ln_connected.shp"
    other_pt = "./intermediate/pt_NARN_LINE_03162018.shp"

    node_id_to_link_ids_dict = get_near_id_to_link_ids_dict("id_min_dist.csv")
    arcpy.CheckOutExtension("Network")
    start_end_ids_dict = {row1.getValue("_ID_"): [row1.getValue("_A_"), row1.getValue("_B_"), row1.getValue("_LEN_")]
                          for row1 in arcpy.SearchCursor(base)}
    nodes_inside = get_all_nodes_in_link(other)
    pool = multiprocessing.Pool()
    #get_distance_blabla(node_id_to_link_ids_dict, near_ids, base, base_f, other, other_f, other_pt,other_pt_f, start_end_ids_dict, 10517)
    func = partial(get_distance_blabla, node_id_to_link_ids_dict, base, other_pt, start_end_ids_dict)
    coord_list = pool.map(func, nodes_inside)
    pool.close()
    pool.join()
    node_coord_dict = {x:y for x,y in zip(nodes_inside,coord_list)}

    pd.DataFrame({key: pd.Series(value) for key, value in node_coord_dict.iteritems()}).transpose().to_csv(
        node_coordinates_dict)
    np.save('./intermediate/node_coord_dict', np.array(dict(node_coord_dict)))

if __name__ == '__main__':
    main()
