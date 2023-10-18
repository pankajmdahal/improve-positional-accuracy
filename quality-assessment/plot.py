import arcpy
import pandas as pd
import csv
from merge import *
import numpy as np

arcpy.env.overwriteOutput = True

# shapefiles
other = "./intermediate/NARN_LINE_03162018.shp"
other_f = "other_f"
arcpy.MakeFeatureLayer_management(other, other_f)

all_dict = np.load('./intermediate/link_route_type_dict.npy').item()

# read from csv files to a dict
no_routes_found_dict = {x: y for x, y in all_dict.items() if y[2] == 1}
routes_out_of_buffer = {x: y for x, y in all_dict.items() if y[2] == 2}
routes_within_buffer = {x: y for x, y in all_dict.items() if y[2] == 3}


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


# create no_route_shp

where_clause = get_where_clause("_ID_", no_routes_found_dict.keys())
arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(other_f, output_no_routes_shp)

# create no_tolerance_within_buffer shp
route_within_threshold_dict = {x: y for x, y in routes_out_of_buffer.iteritems() if
                               ((abs(y[1] - y[0]) / y[0]) > float(threshold) / 100)}
where_clause = get_where_clause("_ID_", route_within_threshold_dict.keys())
arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(other_f, output_tolerance_exceed_shp)
arcpy.AddField_management(output_tolerance_exceed_shp, '_RLENG_', "FLOAT")
arcpy.AddField_management(output_tolerance_exceed_shp, '_TOL_', "FLOAT")
with arcpy.da.UpdateCursor(output_tolerance_exceed_shp, ['_ID_', '_RLENG_', "_LEN_", "_TOL_"]) as cursor:
    for row in cursor:
        row[1] = route_within_threshold_dict[row[0]][1]
        row[3] = abs(row[1] - row[2]) / row[2]
        cursor.updateRow(row)

# create no_tolerance_shp
route_buffer_within_threshold_dict = {x: y for x, y in routes_within_buffer.iteritems() if
                                      ((abs(y[1] - y[0]) / y[0]) > float(threshold) / 100)}

where_clause = get_where_clause("_ID_", route_buffer_within_threshold_dict.keys())
arcpy.SelectLayerByAttribute_management(other_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(other_f, output_buffer_tolerance_exceed_shp)
arcpy.AddField_management(output_buffer_tolerance_exceed_shp, '_RLENG_', "FLOAT")
arcpy.AddField_management(output_buffer_tolerance_exceed_shp, '_TOL_', "FLOAT")
with arcpy.da.UpdateCursor(output_buffer_tolerance_exceed_shp, ['_ID_', '_RLENG_', "_LEN_", "_TOL_"]) as cursor:
    for row in cursor:
        row[1] = route_buffer_within_threshold_dict[row[0]][1]
        row[3] = abs(row[1] - row[2]) / row[2]
        cursor.updateRow(row)
