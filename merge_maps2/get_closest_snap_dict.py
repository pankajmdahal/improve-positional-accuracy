# finding links that are not in the base network

import arcpy
import sys
import csv
import pandas
import os
from merge import *

arcpy.env.overwriteOutput = True

# getting the names of all the shape files
list_of_shp = os.listdir(intermediate_folder)
list_of_shp = [x for x in list_of_shp if '.shp' in x]
remove_list = ['pt', 'ND_Junctions', '_dataset', 'xml', 'lock']
for value in remove_list:
    list_of_shp = [x for x in list_of_shp if value not in x]

list_of_shp = [intermediate_folder + x for x in list_of_shp]
print("List of layers imported {0}".format(list_of_shp))

# base is the one with the highest number of features
count = 0
for shp in list_of_shp:
    count_in_shp = int(arcpy.GetCount_management(shp)[0])
    if count_in_shp > count:
        base = shp
        count = count_in_shp

others = list_of_shp
others.remove(base)

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


for other in others:
    # clipping the shapefile and getting node-coordinate dict
    arcpy.MakeFeatureLayer_management(other, other_f)
    #each link is associated with 2 nodes, make its dictionary
    link_node_dict = {row2.getValue("_ID_"): [row2.getValue("_A_"), row2.getValue("_B_")] for row2 in
                      arcpy.SearchCursor(other_f)}
    nodes_inside = []
    for key, value in link_node_dict.iteritems():
        if value[0] not in nodes_inside:
            nodes_inside.append(value[0])
        if value[1] not in nodes_inside:
            nodes_inside.append(value[1])
        continue

    other_pt = other
    other_pt = other_pt.replace("intermediate/", "intermediate/pt_")
    arcpy.MakeFeatureLayer_management(base, base_f)
    arcpy.MakeFeatureLayer_management(other_pt, other_pt_f)

    # find the nearest coordinates to those links
    near_ids = {}
    no_nearby_linkids = []
    id_buffer_dict = {}
    i = 0
    arcpy.AddSpatialIndex_management(base_f)  # adjusted comment from gis.stackoverflow
    for key in nodes_inside:
        i = i + 1
        if i % 100 == 0:
            pandas.DataFrame({key: pandas.Series(value) for key, value in near_ids.iteritems()}).transpose().to_csv(
                node_coordinates_dict)
            #pandas.DataFrame(no_nearby_linkids).to_csv(no_nearby_dict)
            #pandas.DataFrame.from_dict(id_buffer_dict, orient='index').to_csv(id_buffer_dict)
        print key
        where_clause = """ "_ID_" = %d""" % key
        arcpy.SelectLayerByAttribute_management(other_pt_f, "NEW_SELECTION", where_clause)
        for buffer_dist in buffer_dist_list:
            arcpy.Buffer_analysis(other_pt_f, buffer_shp, buffer_dist)
            arcpy.SelectLayerByLocation_management(base_f, "INTERSECT", buffer_shp, "", "", "")  # takes a long time
            # get IDs of those links
            ids_list = [row.getValue("_ID_") for row in arcpy.SearchCursor(base_f)]
            # remove touching IDs
            if len(ids_list) == 0:
                print "Increasing buffer distance.."
                continue
            else:
                id_buffer_dict[key] = int(buffer_dist.split(" ")[0])
                break
        if len(ids_list) == 0:
            print ("Highest range didn't work")
            no_nearby_linkids.append(key)
            continue
        ids = ids_list
        # ids = remove_touching_linkids(ids_list) # this causes issues for shorter links
        print "Proximite link IDs: {1}".format(len(ids), ids)
        if len(ids) == 0:  # not found upto highest
            continue
        nearxy = []
        for id in ids:
            where_clause = """ "_ID_" = %d""" % id
            arcpy.SelectLayerByAttribute_management(base_f, "NEW_SELECTION", where_clause)
            arcpy.CopyFeatures_management(other_pt_f, m1)
            arcpy.Snap_edit(m1, [[base_f, "EDGE", "1 Miles"]])  # the snap distance is 200f feet for now
            with arcpy.da.SearchCursor(m1, ["SHAPE@XY"]) as curs:
                for xy in curs:
                    nearxy.append(xy[0])
        near_ids[key] = nearxy

pandas.DataFrame({key: pandas.Series(value) for key, value in near_ids.iteritems()}).transpose().to_csv(
    node_coordinates_dict)
pandas.DataFrame(no_nearby_linkids).to_csv(no_nearby_dict)
#pandas.DataFrame.from_dict(id_buffer_dict, orient='index').to_csv(id_buffer_dict)
