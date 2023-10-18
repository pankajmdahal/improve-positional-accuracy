# checks for project, clip, calculate length, get_anode_bnode
import arcpy
import os
import pandas
from merge import *
import math

arcpy.env.overwriteOutput = True

feature_layer = "fl"
mf = "m_feature"

# same projection for all
sr_wgs1984 = arcpy.SpatialReference(4326)

list_of_shp = os.listdir(shp_folder)
list_of_shp = [x for x in list_of_shp if '.shp' in x]
list_of_shp = [x for x in list_of_shp if 'lock' not in x]

def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]

# create clip shp
arcpy.MakeFeatureLayer_management(all_area_shp, all_area_shp_f)
where_clause = get_where_clause("ABBR", clip_state_list)
arcpy.SelectLayerByAttribute_management(all_area_shp_f, "NEW_SELECTION", where_clause)

arcpy.CopyFeatures_management(all_area_shp_f,m)
arcpy.Dissolve_management(m, clip_area_shp, "", "", "SINGLE_PART", "")

for shp in list_of_shp:
    m = shp_folder + shp
    sr_curr_network = arcpy.Describe(m).spatialReference
    # project it to specified projection if else
    if sr_curr_network.name != sr_wgs1984.name:
        print("Projecting to WGS1984...")
        arcpy.Project_management(m, temp_temp, sr_wgs1984)
        arcpy.CopyFeatures_management(temp_temp, m1)
    else:
        arcpy.CopyFeatures_management(m, m1)

    arcpy.MakeFeatureLayer_management(m1, mf)
    clip_area_shp
    arcpy.SelectLayerByLocation_management(mf,"COMPLETELY_WITHIN",clip_area_shp)
    arcpy.CopyFeatures_management(mf, m2)
    print("Clipping to desired area...")
    #
    # check for multipart features
    multipart_dict = {}
    with arcpy.da.SearchCursor(m2, ["OBJECTID", "SHAPE@"]) as cursor:
        for row in cursor:
            count = row[1].partCount
            if count > 1:
                multipart_dict.setdefault(row[0], []).append(count)
    #
    if len(multipart_dict.keys()) > 0:
        print ("Please fix multipart on {0} and run again".format(shp))
        print("LinkID: {0}:".format(multipart_dict))
        pandas.DataFrame(multipart_dict).to_csv(multipart_csv)
        exit(0)
    # put FID, miles, ANODE and BNODE on each
    fieldnames = [f.name for f in arcpy.ListFields(m2)]
    fieldnames = [x for x in fieldnames if x not in ("FID", "Shape", "OBJECTID")]
    # print fieldnames
    # remove everything except
    arcpy.DeleteField_management(m2, fieldnames)
    #add points
    print ("Adding Coordinates to points...")
    arcpy.FeatureVerticesToPoints_management(m2, p1, "BOTH_ENDS")
    #
    arcpy.DeleteIdentical_management(p1, ['Shape'])
    #
    arcpy.AddField_management(p1, "_ID_", "LONG")
    arcpy.CalculateField_management(p1, "_ID_", '!FID!', "PYTHON")
    #
    arcpy.AddField_management(m2, "_ID_", "LONG")
    arcpy.AddField_management(m2, "_LEN_", "DOUBLE")
    arcpy.AddField_management(m2, "_A_", "LONG")
    arcpy.AddField_management(m2, "_B_", "LONG")
    arcpy.CalculateField_management(m2, "_ID_", '!FID!', "PYTHON")
    arcpy.CalculateField_management(m2, "_LEN_", '!Shape.length@miles!', "PYTHON")
    #
    # creating coord-id dict
    coord_to_node_dict = {}
    with arcpy.da.SearchCursor(p1, ["SHAPE@XY","_ID_"], spatial_reference = sr_wgs1984) as cursor:
        for coord,id in cursor:
            coord_to_node_dict[coord[0],coord[1]] = id
    #
    with arcpy.da.UpdateCursor(m2, ["SHAPE@", "_A_", "_B_"], spatial_reference = sr_wgs1984 ) as cursor:
        for row in cursor:
            # get the exact coordinates and map it to the ID
            coord_start = (row[0].firstPoint.X, row[0].firstPoint.Y)
            coord_end = (row[0].lastPoint.X, row[0].lastPoint.Y)
            row[1] = coord_to_node_dict[coord_start]
            row[2] = coord_to_node_dict[coord_end]
            cursor.updateRow(row)
    #
    arcpy.CopyFeatures_management(m2, intermediate_folder + shp)
    arcpy.CopyFeatures_management(p1, intermediate_folder + "pt_" + shp)