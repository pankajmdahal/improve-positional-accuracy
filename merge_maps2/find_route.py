# finding routes that are not

import arcpy
import sys
import csv
import pandas
import os

arcpy.env.overwriteOutput = True

# parameters
buffer_dist = '50 feet'
a_list = []
b_list = []

# getting the names of all the shape files
intermediate_folder = './intermediate/'
list_of_shp = os.listdir(intermediate_folder)
list_of_shp = [x for x in list_of_shp if '.shp' in x]
list_of_shp = [x for x in list_of_shp if 'pt' not in x]
list_of_shp = [x for x in list_of_shp if 'ND_Junctions' not in x]
list_of_shp = [x for x in list_of_shp if '_dataset' not in x]
list_of_shp = [x for x in list_of_shp if 'xml' not in x]
list_of_shp = [x for x in list_of_shp if 'lock' not in x]


list_of_shp = [intermediate_folder + x for x in list_of_shp]
print("List of layers imported {0}".format(list_of_shp))


# shape files
m = "in_memory/T4"
m = "C:/GIS/temp.shp"
feature = "feature"
f = "C:/GIS/temp.shp"
base_f = "base_f"
other_f = "other_f"
buffer_shp = "in_memory/b1"
route_shp = "route_shp"

#output shp
output_no_routes_shp = "C:/GIS/noroutes.shp"
output_tolerance_exceed_shp = "C:/GIS/exceedtolerance.shp"



clip_area_shp = "../shp/clip_area/TN.shp"
temp_shp1 = "C:/GIS/T1.shp"
clipped_dataset = "./intermediate/clipped_dataset.shp"
clipped_dataset_f = "./intermediate/clipped_dataset_f.shp"
clipped_dataset_pt = "./intermediate/pt_clipped_dataset.shp"

network_dataset = "./intermediate/network_dataset.shp"
network_dataset_ND = "./intermediate/network_dataset_ND.nd"

all_dataset = "./intermediate/railway_ln_connected.shp"
all_dataset_ND = "./intermediate/railway_ln_connected_ND.nd"


def str_to_list(value):
    new = value.replace("(","").replace(")","")
    new = new.split(",")
    return new



#csv file
coordinates_df = pandas.read_csv("tocsv.csv").set_index('Unnamed: 0')
coordinates_df = coordinates_df.fillna("?")
coordinates_df = coordinates_df.applymap(str)
coordinates_df = coordinates_df.applymap(str_to_list)
coordinates_df['new'] = coordinates_df['0'] + coordinates_df['1'] +coordinates_df['2']
coordinates_df = coordinates_df[['new']]
coordinates_dict = coordinates_df.to_dict()['new']

coordinates_conv_dict = {}
for key,value in coordinates_dict.iteritems():
    value1 = value
    if '?' in value1:
        value1.remove('?')
        try:
            value1.remove('?')
        except:
            pass
    if len(value1)==2:
        value1 = [list((float(value1[0]),float(value1[1])))]
        #print "2:{0}".format(value1)
    elif len(value1)==4:
        new = [list((float(value1[0]),float(value1[1])))]
        new.append(list((float(value1[2]),float(value1[3]))))
        value1 = new
        #print "4:{0}".format(value1)
    elif len(value1)==6:
        new = [list((float(value1[0]),float(value1[1])))]
        new.append(list((float(value1[2]),float(value1[3]))))
        new.append(list((float(value1[4]),float(value1[5]))))
        value1 = new
        #print "6:{0}".format(value1)
    else:
        print value1
        print "Exception"
        value1 = []
    coordinates_conv_dict[int(key)] = value1


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

node_coordinate_dict = {}

def create_nd_shp(key, _a_,_b_,_len_):
    print "{0}:{1}->{2}".format(key, _a_, _b_)
    # prepare ND
    # use the key to buffer/clip/create ND
    where_clause = """ "_ID_" = %d""" % key
    arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
    arcpy.Buffer_analysis(other_f, buffer_shp, buffer_dist)
    arcpy.SelectLayerByLocation_management(base_f, "INTERSECT", buffer_shp, "", "", "")
    number = []
    with arcpy.da.SearchCursor(base_f, ["_ID_"]) as curs:
        for xy in curs:
            number.append(xy[0])
    print number
    if len(number)<1:
        arcpy.MakeRouteLayer_na(all_dataset_ND, "Route", "Length")
        print "#"
    else:
        arcpy.CopyFeatures_management(base_f, network_dataset)
        arcpy.BuildNetwork_na(network_dataset_ND)
        arcpy.MakeRouteLayer_na(network_dataset_ND, "Route", "Length")
    try:
        return (coordinates_conv_dict[_a_],coordinates_conv_dict[_b_])
    except:
        route_not_found_dict[key] = _len_
        return 0



# functions
def get_length_route(points):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point).projectAs(arcpy.SpatialReference(4326))
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    arcpy.AddLocations_na("Route", "Stops", m, "Name Name #", "0.5 Miles", "", "", "MATCH_TO_CLOSEST", "CLEAR",
                          "NO_SNAP", "10 Meters", "INCLUDE", "")
    arcpy.Solve_na("Route", "SKIP", "TERMINATE", "500 Kilometers")
    arcpy.SelectData_management("Route", "Routes")
    arcpy.FeatureToLine_management("Route\\Routes", f, "", "ATTRIBUTES")
    leng = [row.getValue("Total_Leng") for row in arcpy.SearchCursor(f)][0] / 1609.34
    return leng


def get_where_clause(list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"_ID_" = %d OR """ % id
    return wh_cl[:-4]

arcpy.CheckOutExtension("Network")

for other in others:
    # clip the area (would be removed later when working with entire US)
    arcpy.MakeFeatureLayer_management(other, "temp")
    arcpy.SelectLayerByLocation_management("temp", "INTERSECT", clip_area_shp, "", "", "")  # takes a long time
    arcpy.CopyFeatures_management("temp", clipped_dataset)
    other_pt = other
    other_pt = other_pt.replace("intermediate/", "intermediate/pt_")
    clipped_dataset_pt = other_pt
    print("Clipped Dataset Created..")
    arcpy.MakeFeatureLayer_management(base, base_f)
    print ("working on {0}".format(other))
    arcpy.MakeFeatureLayer_management(other, other_f)
    start_end_ids_dict = {row1.getValue("_ID_"): [row1.getValue("_A_"), row1.getValue("_B_"), row1.getValue("_LEN_")] for row1 in arcpy.SearchCursor(clipped_dataset)}
    #print clipped_dataset_pt
    #node_coordinate_dict = {row2.getValue("_ID_"): [row2.getValue("_X_"), row2.getValue("_Y_")] for row2 in arcpy.SearchCursor(clipped_dataset_pt)}
    route_not_found_dict = {}
    route_tolerance_exceed_dict = {}

for key in start_end_ids_dict.keys():
    _a_ = start_end_ids_dict[key][0]
    _b_ = start_end_ids_dict[key][1]
    _len_ = start_end_ids_dict[key][2]
    dumm = create_nd_shp(key, _a_, _b_, _len_)
    if dumm==0:
        continue #already added to route not found dict
    else:
        (a_list, b_list) = dumm
    distance_list_dict = []
    # x1y1 = a_list[0]
    # x2y2 = b_list[0]
    for x1y1 in a_list:
        for x2y2 in b_list:
            try:
                route_leng = get_length_route([x1y1, x2y2])
            except:
                route_leng = 99999
            distance_list_dict.append(route_leng)

    minimum_distance = min(distance_list_dict)
    if abs((minimum_distance - _len_) / _len_) >= 0.2:
        route_tolerance_exceed_dict[key]=minimum_distance

pandas.DataFrame.from_dict(route_not_found_dict, orient='index').to_csv(no_routes)
pandas.DataFrame.from_dict(route_tolerance_exceed_dict, orient='index').to_csv(no_tolerance)

#create no_route_shp
where_clause = get_where_clause(route_not_found_dict.keys())
arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(other_f,output_no_routes_shp )

#create no_tolerance_shp
where_clause = get_where_clause(route_tolerance_exceed_dict.keys())
print where_clause
arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(other_f,output_tolerance_exceed_shp )
arcpy.AddField_management(output_tolerance_exceed_shp,'_RLENG_',"FLOAT")
with arcpy.da.UpdateCursor(output_tolerance_exceed_shp, ['_ID_','_RLENG_']) as cursor:
    for row in cursor:
        row[1] = route_tolerance_exceed_dict[row[0]]
        cursor.updateRow(row)

