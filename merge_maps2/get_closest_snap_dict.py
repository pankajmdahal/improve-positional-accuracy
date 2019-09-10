# finding routes that are not

import arcpy
import sys
import csv
import pandas
import os

arcpy.env.overwriteOutput = True

# parameters, keep on going to 200 feet if not found
buffer_dist_list = ['20 feet','40 feet','60 feet','80 feet','100 feet','120 feet', '140 feet','160 feet','180 feet','200 feet']

# getting the names of all the shape files
intermediate_folder = './intermediate/'
list_of_shp = os.listdir(intermediate_folder)
list_of_shp = [x for x in list_of_shp if '.shp' in x]

remove_list = ['pt', 'ND_Junctions', '_dataset', 'xml', 'lock']
for value in remove_list:
    list_of_shp = [x for x in list_of_shp if value not in x]

list_of_shp = [intermediate_folder + x for x in list_of_shp]
print("List of layers imported {0}".format(list_of_shp))

# shape files
m = "in_memory/T4"
m1 = "in_memory/T5"
#f = "C:/GIS/temp.shp"
f = "in_memory/T2"
base_f = "base_f"
other_f = "other_f"
#buffer_shp = "C:/GIS/buffer.shp"
buffer_shp = "in_memory/B1"
#route_shp = "route_shp"

clip_area_shp = "../shp/clip_area/TN.shp"
#temp_shp1 = "C:/GIS/T1.shp"
temp_shp1 = "in_memory/T1"
clipped_dataset = "in_memory/c2"
clipped_dataset_f = "clipped_f"
clipped_dataset_pt = "in_memory/c1"
clipped_dataset_pt_f = "clipped_pt_f"
other_pt_f = "other_pt"

network_dataset = "./intermediate/network_dataset.shp"
network_dataset_ND = "./intermediate/network_dataset_ND.nd"

# base is the one with the highest number of features
count = 0
for shp in list_of_shp:
    count_in_shp = int(arcpy.GetCount_management(shp)[0])
    if count_in_shp > count:
        base = shp
        count = count_in_shp

others = list_of_shp
others.remove(base)

# csv files
no_routes = "noroutes.csv"
no_tolerance = "notolerance.csv"

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
    arcpy.MakeFeatureLayer_management(other, "temp1")
    # arcpy.SelectLayerByLocation_management("temp1", "INTERSECT", clip_area_shp, "", "", "")  # takes a long time
    # arcpy.CopyFeatures_management("temp1", clipped_dataset)
    clipped_dataset = "temp1"
    link_node_dict = {row2.getValue("_ID_"): [row2.getValue("_A_"), row2.getValue("_B_")] for row2 in arcpy.SearchCursor(clipped_dataset)}
    nodes_inside = []
    for key, value in link_node_dict.iteritems():
        if value[0] not in nodes_inside:
            nodes_inside.append(value[0])
        if value[1] not in nodes_inside:
            nodes_inside.append(value[1])
        continue

    other_pt = other
    other_pt = other_pt.replace("intermediate/", "intermediate/pt_")
    #node_coordinates_dict = {row2.getValue("_ID_"): [row2.getValue("_X_"), row2.getValue("_Y_")] for row2 in arcpy.SearchCursor(other_pt)}
    #clipped_coordinates_dict = {x:[node_coordinates_dict[x][0],node_coordinates_dict[x][1]] for x in nodes_inside}

    arcpy.MakeFeatureLayer_management(base, base_f)
    arcpy.MakeFeatureLayer_management(other_pt, other_pt_f)

    # find the nearest coordinates to those links
    near_ids = {}
    no_nearby_linkids = []
    id_buffer_dict = {}
    i=0
    arcpy.AddSpatialIndex_management(base_f) #adjusted comment from gis.stackoverflow
    for key in nodes_inside:
        i=i+1
        if i%100 == 0:
            pandas.DataFrame({key: pandas.Series(value) for key, value in near_ids.iteritems()}).transpose().to_csv("tocsv.csv")
            pandas.DataFrame(no_nearby_linkids).to_csv("no_nearby.csv")
            pandas.DataFrame.from_dict(id_buffer_dict, orient = 'index').to_csv("id_buffer_dict.csv")
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
        #ids = remove_touching_linkids(ids_list) # this causes issues for shorter links
        print "Proximite link IDs: {1}".format(len(ids),ids)
        if len(ids) == 0: #not found upto highest
            continue
        nearxy = []
        for id in ids:
            where_clause = """ "_ID_" = %d""" % id
            arcpy.SelectLayerByAttribute_management(base_f, "NEW_SELECTION", where_clause)
            arcpy.CopyFeatures_management(other_pt_f, m1)
            arcpy.Snap_edit(m1, [[base_f, "EDGE", "1 Miles"]]) #the snap distance is 200f feet for now
            with arcpy.da.SearchCursor(m1, ["SHAPE@XY"]) as curs:
                for xy in curs:
                    nearxy.append(xy[0])
        near_ids[key] = nearxy

pandas.DataFrame({key: pandas.Series(value) for key, value in near_ids.iteritems()}).transpose().to_csv("tocsv.csv")
pandas.DataFrame(no_nearby_linkids).to_csv("no_nearby.csv")
pandas.DataFrame.from_dict(id_buffer_dict, orient = 'index').to_csv("id_buffer_dict.csv")