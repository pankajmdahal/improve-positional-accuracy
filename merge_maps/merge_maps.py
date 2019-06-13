# finding routes that are not

import arcpy
import sys
import csv
import pandas


arcpy.env.overwriteOutput = True

# shape files
clip_area_shp = "../shp/clip_area/TN.shp"
base = "../shp/railway_ln_connected/railway_ln_connected.shp"
link_lists = ["../shp/NARN/NARN_LINE_03162018.shp"]
base_nd = "../shp/railway_ln_connected/railway_ln_connected_ND.nd"

#build layer
arcpy.CheckOutExtension("Network")
#arcpy.BuildNetwork_na(base_nd) #because the file may have been changed
print("Network Rebuilt")
arcpy.MakeRouteLayer_na(base_nd, "Route", "Length")

# temp files
temp_shp1 = "in_memory/T1"
temp_shp2 = "in_memory/T2"
temp_shp3 = "in_memory/T3"
m = "in_memory/T4"

temp_shp1 = "C:/GIS/T1.shp"
temp_shp2 = "C:/GIS/T2.shp"
temp_shp3 = "C:/GIS/T3.shp"
m = "C:/GIS/T4.shp"



#m = "C:/GIS/temp99.shp"

f = "C:/GIS/temp.shp"

# csv files
no_routes = "noroutes.csv"
no_tolerance = "notolerance.csv"


# functions
def create_shp(points):
    point = arcpy.Point()
    pointGeometryList = []
    for pt in points:
        point.X = pt[0]
        point.Y = pt[1]
        pointGeometry = arcpy.PointGeometry(point)
        pointGeometryList.append(pointGeometry)
    arcpy.CopyFeatures_management(pointGeometryList, m)
    #arcpy.DefineProjection_management(m, arcpy.SpatialReference(4326))



#(clip the overlaying layer) and get length (in miles) and get coordinates
def shp_to_start_end_coordinates(link):
    dummdict = {}
    arcpy.MakeFeatureLayer_management(link,"temp")
    arcpy.SelectLayerByLocation_management("temp", "INTERSECT", clip_area_shp, "", "", "")  # takes a long time
    arcpy.CopyFeatures_management("temp",temp_shp1)
    #arcpy.Clip_analysis(link, clip_area_shp, temp_shp1)
    arcpy.AddField_management(temp_shp1, "LENGTH", "DOUBLE")
    arcpy.CalculateField_management(temp_shp1, "LENGTH", '!Shape.length@miles!', "PYTHON")
    arcpy.FeatureVerticesToPoints_management(temp_shp1, temp_shp2, "BOTH_ENDS")
    sr = arcpy.SpatialReference(4326)
    with arcpy.da.SearchCursor(temp_shp2, ["OBJECTID", "SHAPE@XY", "Length"], spatial_reference=sr) as curs:
        for id2, xy, len in curs:
            if id2 in dummdict.keys():
                dummdict[id2] = [dummdict[id2][0], xy, len]
            else:
                dummdict[id2] = [xy, [], len]
    return dummdict

a_df = pandas.DataFrame()
b_df = pandas.DataFrame()

for link in link_lists:
    start_end_length_dict = shp_to_start_end_coordinates(link)
    route_not_found_dict = {}
    route_tolerance_exceed_dict = {}
    # check routes
    for key,value in start_end_length_dict.iteritems():
        start = value[0]
        end = value[1]
        length = value[2]
        create_shp([start, end])

        arcpy.AddLocations_na("Route", "Stops", m, "Name Name #", "0.5 Miles", "","", "MATCH_TO_CLOSEST", "CLEAR", "NO_SNAP", "5 Meters","INCLUDE", "")
        try:
            arcpy.Solve_na("Route", "SKIP", "TERMINATE", "500 Kilometers")
            arcpy.SelectData_management("Route", "Routes")
            arcpy.FeatureToLine_management("Route\\Routes", f, "", "ATTRIBUTES")
            route_leng = [row.getValue("Total_Leng") for row in arcpy.SearchCursor(f)][0]/1609.34
            sys.stdout.write('.')
        except:
            sys.stdout.write('*')
            route_not_found_dict[key]=length
            continue
        if abs((route_leng - length) / length) >= 0.1:
            print("^")
            route_tolerance_exceed_dict[key] = [route_leng,length]

        pandas.DataFrame.from_dict(route_not_found_dict, orient='index').to_csv(no_routes)
        pandas.DataFrame.from_dict(route_tolerance_exceed_dict, orient='index').to_csv(no_tolerance)
