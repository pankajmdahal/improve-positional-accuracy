#get required shapes and validate
import arcpy
from parameters import *
import timeit

arcpy.env.overwriteOutput = True

linksn_f = "linksf"


links_o = old_links_shp  # use this area to crop the new link
links_n = new_links_clipped  # cropped area would be outputted to this file
nodes_n = new_nodes_shp  # the nodes calculated from new links would be outputted here
nodes_o = old_nodes_shp  # the nodes calculated from old links would be outputted here


if extent_switch ==1: #the new network is significantly bigger than the old, so it has to be cropped
    #crop the area of the network (use only the extent of the old network)
    arcpy.MakeFeatureLayer_management(new_links_shp, linksn_f)
    arcpy.MakeFeatureLayer_management(links_o, "bufferf")
    arcpy.Buffer_analysis(links_o, "in_memory/buffer", clip_distance)
    arcpy.Dissolve_management("in_memory/buffer", temp)
    arcpy.SelectLayerByLocation_management(linksn_f, "INTERSECT", temp, "", "NEW_SELECTION")
    arcpy.CopyFeatures_management(linksn_f, links_n)

else:
    links_n = new_links_shp

#get new nodes
arcpy.AddField_management(links_n, "_ID_", "LONG")
arcpy.CalculateField_management(links_n, "_ID_", '!FID!', "PYTHON")
arcpy.FeatureVerticesToPoints_management(links_n, nodes_n, "BOTH_ENDS")
arcpy.DeleteIdentical_management(nodes_n, ['Shape'])
arcpy.AddField_management(nodes_n, "_ID_", "LONG")
arcpy.CalculateField_management(nodes_n, "_ID_", '!FID!', "PYTHON")
fieldnames = [x for x in [f.name for f in arcpy.ListFields(nodes_n)] if x not in ['FID', 'Shape', 'OID', "_ID_"]]
arcpy.DeleteField_management(nodes_n, fieldnames)

# get old nodes
arcpy.AddField_management(links_o, "_ID_", "LONG")
arcpy.CalculateField_management(links_o, "_ID_", '!FID!', "PYTHON")
arcpy.FeatureVerticesToPoints_management(links_o, nodes_o, "BOTH_ENDS")
arcpy.DeleteIdentical_management(nodes_o, ['Shape'])
arcpy.AddField_management(nodes_o, "_ID_", "LONG")
arcpy.CalculateField_management(nodes_o, "_ID_", '!FID!', "PYTHON")
fieldnames = [x for x in [f.name for f in arcpy.ListFields(nodes_o)] if x not in ['FID', 'Shape', '_ID_']]
arcpy.DeleteField_management(nodes_o, fieldnames)

# snap nodes to calculate routes
arcpy.Copy_management(nodes_o, snapped_old_nodes)  # the old nodes are snapped to the new link, to calculate the sum distance

arcpy.Snap_edit(snapped_old_nodes, [[links_n, "EDGE", near_snap_dist]])





