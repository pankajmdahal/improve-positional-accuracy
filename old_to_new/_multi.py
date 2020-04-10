# work on IDs not FIDs, IDs never change, FIDs do
import pandas
import arcpy
from parameters import *
import random
import numpy as np
import multiprocessing

m = "in_memory/m11"
m = "C:/GIS/m.shp"

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



def get_dist(points):
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
    arcpy.Solve_na(B1_route, "SKIP", "TERMINATE", "")
    arcpy.SelectData_management(B1_route, "Routes")
    arcpy.FeatureToLine_management(B1_route + "/Routes", feature, "", "ATTRIBUTES")
    return [f[0] for f in arcpy.da.SearchCursor(feature, 'SHAPE@LENGTH')]




x1y1 = (-83.9431603,35.9594551)
x2y2 = (-85.3290596,35.0139442)
point = [x1y1, x2y2]

pool = multiprocessing.Pool()
pool.map(get_dist, point)
pool.close()
pool.join()

distance = get_dist(point)