import arcpy
import os


matches = []
rootPath = "C:/Users/pankaj/Desktop/test"
rootPath = os.getcwd()

for root, dirs, files in os.walk(rootPath):
    for filename in files:
        if filename == "gis_osm_railways_free_1.shp":
            match = ( os.path.join(root, filename))
            matches.append (match)

arcpy.Merge_management(matches, rootPath + "/output/railway_ln.shp")


#generate different types of railway_ln shp
#1 continuous and with no attributes

#2 discontinuous but with attributes