import arcpy
from parameters import *

arcpy.env.overwriteOutput = True

linksn_f = "linksf"


links_o = old_links_cropped_shp #use this area to crop the new link
links_n = new_links_clipped #cropped area would be outputted to this file
nodes_n = new_nodes_shp #the nodes calculated from new links would be outputted here
nodes_o = old_nodes_shp #the nodes calculated from old links would be outputted here


#selection would be done from all links (obviously)
arcpy.MakeFeatureLayer_management(new_links_shp, linksn_f)


#crop the area of the network
arcpy.MakeFeatureLayer_management(links_o, "bufferf")
arcpy.Buffer_analysis (links_o, "in_memory/buffer", clip_distance)
arcpy.Dissolve_management("in_memory/buffer",temp)
arcpy.SelectLayerByLocation_management(linksn_f, "INTERSECT", temp, "", "NEW_SELECTION")
arcpy.CopyFeatures_management(linksn_f, links_n)




#get new nodes (calculate this)
arcpy.FeatureVerticesToPoints_management(links_n, nodes_n, "BOTH_ENDS")
arcpy.AddField_management(nodes_n, "_X_", "DOUBLE")
arcpy.AddField_management(nodes_n, "_Y_", "DOUBLE")
with arcpy.da.UpdateCursor(nodes_n, ["SHAPE@XY", "_X_", "_Y_"]) as cursor:
    for row in cursor:
        row[1] = row[0][0]
        row[2] = row[0][1]
        cursor.updateRow(row)

arcpy.DeleteIdentical_management(nodes_n, ['_X_', '_Y_'])
arcpy.AddField_management(nodes_n, "_ID_", "LONG")
arcpy.CalculateField_management(nodes_n, "_ID_", '!FID!', "PYTHON")
fieldnames = [f.name for f in arcpy.ListFields(nodes_n)]
fieldnames = [x for x in fieldnames if x not in ['FID', 'Shape', 'OID', "_ID_"]]
for field in fieldnames:
    arcpy.DeleteField_management(nodes_n, field)


#get old nodes from link
arcpy.FeatureVerticesToPoints_management(links_o, nodes_o, "BOTH_ENDS")
arcpy.AddField_management(nodes_o, "_X_", "DOUBLE")
arcpy.AddField_management(nodes_o, "_Y_", "DOUBLE")
with arcpy.da.UpdateCursor(nodes_o, ["SHAPE@XY", "_X_", "_Y_"]) as cursor:
    for row in cursor:
        row[1] = row[0][0]
        row[2] = row[0][1]
        cursor.updateRow(row)

arcpy.DeleteIdentical_management(nodes_o, ['_X_', '_Y_'])
arcpy.AddField_management(nodes_o, "ID", "LONG")
arcpy.CalculateField_management(nodes_o, "ID", '!FID!', "PYTHON")
fieldnames = [f.name for f in arcpy.ListFields(nodes_o)]
fieldnames = [x for x in fieldnames if x not in ['FID', 'Shape', 'ID']]
for field in fieldnames:
    arcpy.DeleteField_management(nodes_o, field)


#snap nodes to calculate routes

arcpy.Copy_management(nodes_o, snapped_old_nodes)
arcpy.Snap_edit(snapped_old_nodes, [[links_n, "EDGE", near_snap_dist]]) #takes very long time


