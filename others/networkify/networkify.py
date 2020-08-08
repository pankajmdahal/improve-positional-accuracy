import arcpy
import numpy as np
import pandas as pd


arcpy.env.overwriteOutput = True


snap_distance = 0.1 #Mile
xy_tolerance = 1 #feet (consecutive links with node connected both are connected to each other)


links = "../shp/NHP/nhpnv14-05shp/NHPNLine.shp"



memory = "C:/GIS/deletethis.shp"
memory1 = "C:/GIS/deletethis1.shp"
memory2 = "C:/GIS/deletethis2.shp"
memory3 = "C:/GIS/deletethis3.shp"
memory4 = "C:/GIS/deletethis3.shp"
memory5 = "C:/GIS/deletethis3.shp"
memory6 = "C:/GIS/deletethis3.shp"
memory7 = "C:/GIS/deletethis3.shp"
dumm_table = "C:/GIS/dummtable1.dbf"


#feature to line


# preparing data (dissolve everything and put back nodes at intersections, WARNING: grade separated stuffs are gone)
arcpy.Dissolve_management(links, memory1, "", "", "SINGLE_PART", "UNSPLIT_LINES")
arcpy.FeatureToLine_management(memory1, memory2, "{0} Feet".format(xy_tolerance), "NO_ATTRIBUTES")


#getting endpoints of links and adding XY
arcpy.FeatureVerticesToPoints_management(memory2, memory3, "BOTH_ENDS")
arcpy.AddXY_management(memory3)

#change it to a dataframe and remove the nodes whose occurances are >1
arr = arcpy.da.TableToNumPyArray(memory3, ['FID', 'POINT_X', 'POINT_Y'])
df = pd.DataFrame(arr)
df['combined'] = df['POINT_X'] * df['POINT_Y']
count_dict = dict(df['combined'].value_counts(dropna=True))
df['occurances'] = df['combined'].map(count_dict)
df_new = df[df.occurances < 2]
xy = zip(df_new['POINT_X'],df_new['POINT_Y'])

#change the dataframe to a shapefile
points = arcpy.Point()
point_geometry = []
for x,y in xy:
    points.X = x
    points.Y = y
    point_geometry.append(arcpy.PointGeometry(points))

arcpy.CopyFeatures_management(point_geometry, memory5)
arcpy.DefineProjection_management (memory5, arcpy.SpatialReference(4326))


#create a copy of link and delete the touching links
arcpy.CopyFeatures_management(memory2,memory7)
arcpy.MakeFeatureLayer_management(memory7, "memory7")
arcpy.SelectLayerByLocation_management("memory7", "INTERSECT", memory2, "", "NEW_SELECTION", "NOT_INVERT")
arcpy.DeleteFeatures_management("memory7")


#select nodes that are at specific distance and export
arcpy.MakeFeatureLayer_management(memory5, "memory5")
arcpy.SelectLayerByLocation_management("memory5", "WITHIN_A_DISTANCE", memory7, str(snap_distance)+ " Miles")
arcpy.CopyFeatures_management("memory5", memory6)


