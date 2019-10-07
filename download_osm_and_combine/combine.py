import arcpy
import os

arcpy.env.overwriteOutput = True

matches = []
rootPath = os.getcwd()
output_path = "/output/highway_ln.shp"
output = rootPath + output_path

m1 = "m1"
feature_layer = "feature"


# arcpy.Copy_management("C:/GIS/empty_shp_line.shp", merged)

for root, dirs, files in os.walk(rootPath):
    for filename in files:
        if filename == "gis_osm_roads_free_1.shp":
            match = (os.path.join(root, filename))
            matches.append(match) #match contains list of all roads shapefiles


field_names = ['bridleway','cycleway','footway','living_street','pedestrian','residential','tertiary_link','service','unclassified','steps','path','tertiary','track', 'track_grade1','track_grade2', 'track_grade3', 'track_grade4', 'track_grade5', 'unknown', 'primary_link', 'secondary_link','trunk_link']

#now adding speed limits
speed_limit_dict = {
    'motorway':55,
    'motorway_link':30,
    'primary':40,
    'primary_link':15,
    'secondary':40,
    'secondary_link':10,
    'trunk':45,
    'trunk_link':15
}

#reducing the size
for path in matches:
    field_str = "', '".join (field_names)
    where_clause = "fclass NOT IN ('{}')".format(field_str)
    path_export = path.replace("gis_osm_roads_free_1.shp", "road_cropped.shp")
    arcpy.MakeFeatureLayer_management(path, feature_layer, where_clause)
    # arcpy.SelectLayerByAttribute_management(feature_layer, "NEW_SELECTION", where_clause)
    #arcpy.GetCount_management(feature_layer)
    arcpy.CopyFeatures_management(feature_layer, path_export)
    arcpy.AddField_management(path_export, "speed","SHORT")
    with arcpy.da.UpdateCursor(path_export, ["fclass", "speed"]) as cursor:
        for row in cursor:
            row[1] = speed_limit_dict[row[0]]
            cursor.updateRow(row)
    arcpy.DeleteField_management(path_export, ["osm_id", "code", "fclass", 'name', "tunnel", "bridge", "ref", "oneway", "maxspeed", "layer", 'new'])

#now
new_matches = []
for root, dirs, files in os.walk(rootPath):
    for filename in files:
        if filename == "road_cropped.shp":
            match = (os.path.join(root, filename))
            new_matches.append(match) #match contains list of all roads shapefiles



# assign first item as target
target = "./output/highway_ln.shp"
arcpy.CopyFeatures_management(new_matches[0],target)

# iterate over remaining files, appending each one to target
for shp in new_matches[1:]:
    print("Appending - {}".format(shp))
    arcpy.Append_management(shp, target)

#add field length
#arcpy.AddField_management(path_export, "leng","DOUBLE")



