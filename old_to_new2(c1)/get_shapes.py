#get required shapes and validate
import arcpy
from parameters import *
import timeit

arcpy.env.overwriteOutput = True

linksn_f = "linksf"
im_t = "in_memory/pp"


links_o = old_links_shp  # use this area to crop the new link
links_n = new_links_clipped  # cropped area would be outputted to this file
nodes_n = new_nodes_shp  # the nodes calculated from new links would be outputted here
nodes_o = old_nodes_shp  # the nodes calculated from old links would be outputted here


if extent_switch ==1: #the new network is significantly bigger than the old, so it has to be cropped
    #crop the area of the network (use only the extent of the old network)
    arcpy.MakeFeatureLayer_management(new_links_shp, linksn_f)
    arcpy.MakeFeatureLayer_management(links_o, "bufferf")
    arcpy.Buffer_analysis(links_o, im_t, clip_distance, "", "", "ALL", "","")
    arcpy.SelectLayerByLocation_management(linksn_f, "COMPLETELY_WITHIN", im_t, "", "NEW_SELECTION")
    FindDisconnectedFeaturesInGeometricNetwork_management(linksn_f, "C:/GIS/temp.shp")

    arcpy.CopyFeatures_management(linksn_f, im_t)


else:
    links_n = new_links_shp

#get new nodes
arcpy.AddField_management(links_n, "_ID_", "LONG")
arcpy.CalculateField_management(links_n, "_ID_", '!FID!', "PYTHON")
arcpy.FeatureVerticesToPoints_management(links_n, im_t, "BOTH_ENDS")
arcpy.DeleteIdentical_management(im_t, ['Shape'])
arcpy.AddField_management(im_t, "_ID_", "LONG")
arcpy.CalculateField_management(im_t, "_ID_", '!FID!', "PYTHON")
fieldnames = [x for x in [f.name for f in arcpy.ListFields(im_t)] if x not in ['FID', 'Shape', 'OID', "_ID_"]]
arcpy.DeleteField_management(im_t, fieldnames)
arcpy.CopyFeatures_management(im_t, nodes_n)

# get old nodes
arcpy.AddField_management(links_o, "_ID_", "LONG")
arcpy.CalculateField_management(links_o, "_ID_", '!FID!', "PYTHON")
arcpy.FeatureVerticesToPoints_management(links_o, im_t, "BOTH_ENDS")
arcpy.DeleteIdentical_management(im_t, ['Shape'])
arcpy.AddField_management(im_t, "_ID_", "LONG")
arcpy.CalculateField_management(im_t, "_ID_", '!FID!', "PYTHON")
fieldnames = [x for x in [f.name for f in arcpy.ListFields(im_t)] if x not in ['FID', 'Shape', '_ID_']]
arcpy.DeleteField_management(im_t, fieldnames)
arcpy.CopyFeatures_management(im_t, nodes_o)

# snap nodes to calculate routes
arcpy.CopyFeatures_management(nodes_o, snapped_old_nodes)  # the old nodes are snapped to the new link, to calculate the sum distance
arcpy.Snap_edit(snapped_old_nodes, [[links_n, "EDGE", near_snap_dist]])





