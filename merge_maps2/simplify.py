# checks for multipart, creates nodes, calculate length
import arcpy
import os
import pandas
from merge import *

arcpy.env.overwriteOutput = True

# same projection for all
sr = arcpy.SpatialReference(4326)

list_of_shp = os.listdir(shp_folder)
list_of_shp = [x for x in list_of_shp if '.shp' in x]

for shp in list_of_shp:
    m = shp_folder + shp
    sr1 = arcpy.Describe(m).spatialReference
    # project it to specified projection if else
    if sr1.name != sr.name:
        print("Projecting to WGS1984...")
        arcpy.Project_management(m, temp, sr)
        arcpy.CopyFeatures_management(temp, m1)
        print("Done")
    else:
        arcpy.CopyFeatures_management(m, m1)

    # check for multipart features
    multipart_list = []
    with arcpy.da.SearchCursor(m1, ["OBJECTID", "SHAPE@"]) as cursor:
        for row in cursor:
            count = row[1].partCount
            if count > 1:
                multipart_list.append(row[0])

    if len(multipart_list) > 0:
        print ("Please fix multipart on {0}".format(shp))
        pandas.DataFrame(multipart_list).to_csv(multipart_csv)
        continue

    # put FID, miles, ANODE and BNODE on each
    fieldnames = [f.name for f in arcpy.ListFields(m1)]
    fieldnames = [x for x in fieldnames if x not in ("FID", "Shape")]
    # print fieldnames
    # remove everything except
    arcpy.DeleteField_management(m1, fieldnames)

    arcpy.AddField_management(m1, "_ID_", "LONG")
    arcpy.AddField_management(m1, "_LEN_", "DOUBLE")
    arcpy.CalculateField_management(m1, "_ID_", '!FID!', "PYTHON")
    arcpy.CalculateField_management(m1, "_LEN_", '!Shape.length@miles!', "PYTHON")

    arcpy.AddField_management(m1, "_A_", "LONG")
    arcpy.AddField_management(m1, "_B_", "LONG")

    arcpy.FeatureVerticesToPoints_management(m1, p1, "BOTH_ENDS")
    arcpy.AddField_management(p1, "_X_", "DOUBLE")
    arcpy.AddField_management(p1, "_Y_", "DOUBLE")

    with arcpy.da.UpdateCursor(p1, ["SHAPE@XY", "_X_", "_Y_"]) as cursor:
        for row in cursor:
            row[1] = row[0][0]
            row[2] = row[0][1]
            cursor.updateRow(row)
    for f in ["ORIG_FID", "Id", "_ID_", "_LEN_", "_A_", "_B_"]:
        arcpy.DeleteField_management(p1, f)
    # since points are created on each end, they overlap (remove them)
    arcpy.DeleteIdentical_management(p1, ['_X_', '_Y_'])
    arcpy.AddField_management(p1, "_ID_", "LONG")
    arcpy.CalculateField_management(p1, "_ID_", '!FID!', "PYTHON")

    # creating coord-id dict
    nodeid_coord_dict = {}
    with arcpy.da.SearchCursor(p1, ["_ID_", "_X_", "_Y_"]) as cursor:
        for row in cursor:
            nodeid_coord_dict[(row[1], row[2])] = row[0]
    with arcpy.da.UpdateCursor(m1, ["SHAPE@", "_A_", "_B_"]) as cursor:
        for row in cursor:
            # get the exact coordinates and map it to the ID
            coord_start = (row[0].firstPoint.X, row[0].firstPoint.Y)
            coord_end = (row[0].lastPoint.X, row[0].lastPoint.Y)
            row[1] = nodeid_coord_dict[coord_start]
            row[2] = nodeid_coord_dict[coord_end]
            cursor.updateRow(row)

    arcpy.CopyFeatures_management(m1, intermediate_folder + shp)
    arcpy.CopyFeatures_management(p1, intermediate_folder + "pt_" + shp)
