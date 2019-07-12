# finding routes that are not

import arcpy
import sys
import csv
import pandas
import os

arcpy.env.overwriteOutput = True

# parameters
buffer_dist = '50 feet'

# getting the names of all the shape files
intermediate_folder = './intermediate/'
list_of_shp = os.listdir(intermediate_folder)
list_of_shp = [x for x in list_of_shp if '.shp' in x]
list_of_shp = [x for x in list_of_shp if 'pt' not in x]
list_of_shp = [x for x in list_of_shp if 'ND_Junctions' not in x]
list_of_shp = [x for x in list_of_shp if '_dataset' not in x]
list_of_shp = [x for x in list_of_shp if 'xml' not in x]


list_of_shp = [intermediate_folder + x for x in list_of_shp]
print("List of layers imported {0}".format(list_of_shp))


# shape files
m = "in_memory/T4"
feature = "feature"
f = "C:/GIS/temp.shp"
base_f = "base_f"
other_f = "other_f"
buffer_shp = "in_memory/b1"
route_shp = "route_shp"

clip_area_shp = "../shp/clip_area/TN.shp"
temp_shp1 = "C:/GIS/T1.shp"
clipped_dataset = "./intermediate/clipped_dataset.shp"
clipped_dataset_f = "./intermediate/clipped_dataset_f.shp"
clipped_dataset_pt = "./intermediate/pt_clipped_dataset.shp"

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


# functions
def get_length_route(points):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point)
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    try:
        arcpy.AddLocations_na("Route", "Stops", m, "Name Name #", "0.5 Miles", "", "", "MATCH_TO_CLOSEST", "CLEAR",
                              "NO_SNAP", "5 Meters", "INCLUDE", "")
        arcpy.Solve_na("Route", "SKIP", "TERMINATE", "500 Kilometers")
        arcpy.SelectData_management("Route", "Routes")
        arcpy.FeatureToLine_management("Route\\Routes", f, "", "ATTRIBUTES")
        leng = [row.getValue("Total_Leng") for row in arcpy.SearchCursor(f)][0] / 1609.34
        return leng
    except:
        return 99999


arcpy.CheckOutExtension("Network")

for other in others:
    # clip the area (would be removed later when working with entire US)
    arcpy.MakeFeatureLayer_management(other, "temp")
    arcpy.SelectLayerByLocation_management("temp", "INTERSECT", clip_area_shp, "", "", "")  # takes a long time
    arcpy.CopyFeatures_management("temp", clipped_dataset)
    other_pt = other
    other_pt = other_pt.replace("intermediate/", "intermediate/pt_")
    # arcpy.MakeFeatureLayer_management(other_pt, "temp1")
    # arcpy.SelectLayerByLocation_management("temp1", "INTERSECT", clip_area_shp, "", "", "")  # takes a long time
    # arcpy.CopyFeatures_management("temp1", clipped_dataset_pt)
    clipped_dataset_pt = other_pt
    print("Clipped Dataset Created..")
    arcpy.MakeFeatureLayer_management(base, base_f)

    print ("working on {0}".format(other))
    arcpy.MakeFeatureLayer_management(other, other_f)
    start_end_ids_dict = {row1.getValue("_ID_"): [row1.getValue("_A_"), row1.getValue("_B_"), row1.getValue("_LEN_")] for row1 in arcpy.SearchCursor(clipped_dataset)}
    print clipped_dataset_pt
    node_coordinate_dict = {row2.getValue("_ID_"): [row2.getValue("_X_"), row2.getValue("_Y_")] for row2 in arcpy.SearchCursor(clipped_dataset_pt)}
    route_not_found_dict = {}
    route_tolerance_exceed_dict = {}
    for key, [_a_, _b_, _len_] in start_end_ids_dict.iteritems():
        _a_coord = node_coordinate_dict[_a_]
        _b_coord = node_coordinate_dict[_b_]
        print("Working on {0}->{1}".format(_a_coord, _b_coord))

        # use the key to buffer/clip/create ND
        where_clause = """ "_ID_" = %d""" % key
        arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
        arcpy.Buffer_analysis(other_f, buffer_shp, buffer_dist)

        arcpy.SelectLayerByLocation_management(base_f, "INTERSECT", buffer_shp, "", "", "")
        arcpy.CopyFeatures_management(base_f, network_dataset)
        arcpy.BuildNetwork_na(network_dataset_ND)
        arcpy.MakeRouteLayer_na(network_dataset_ND, "Route", "Length")

        # find a way to find out other coordinates
        # a loop to select other coordinates

        route_leng = get_length_route([_a_coord, _b_coord])
        if route_leng == 99999:
            sys.stdout.write('*')
            route_not_found_dict[key] = _len_
            continue

        if abs((route_leng - _len_) / _len_) >= 0.1:
            print("^")
            route_tolerance_exceed_dict[key] = [route_leng, _len_]

    pandas.DataFrame.from_dict(route_not_found_dict, orient='index').to_csv(no_routes)
    pandas.DataFrame.from_dict(route_tolerance_exceed_dict, orient='index').to_csv(no_tolerance)
