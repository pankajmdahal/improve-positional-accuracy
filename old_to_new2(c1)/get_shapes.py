#get required shapes and validate
import arcpy
from parameters import *
import timeit

arcpy.env.overwriteOutput = True
arcpy.env.outputMFlag = "Disabled"
# Set the outputZFlag environment to Disabled
arcpy.env.outputZFlag = "Disabled"

linksn_f = "linksf"
im_t = "in_memory/pp"
#im_t = "C:/GIS/temp.shp"


links_o = old_links_shp  # use this area to crop the new link
links_n = new_links_clipped  # cropped area would be outputted to this file
nodes_n = new_nodes_shp  # the nodes calculated from new links would be outputted here
nodes_o = old_nodes_shp  # the nodes calculated from old links would be outputted here


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]

def extract_connected_links(line_feature, output_feature):
    fid = [58004, 84356]
    f1 = "fff1"
    f2 = "fff2"
    connected_dict = {}
    arcpy.MakeFeatureLayer_management(line_feature, f1)
    arcpy.MakeFeatureLayer_management(line_feature, f2)
    arcpy.SelectLayerByAttribute_management(f1, "NEW_SELECTION", get_where_clause("FID", fid))
    count_old = 0
    while True:
        print count_old
        arcpy.SelectLayerByLocation_management(f2, "INTERSECT", f1, "", "ADD_TO_SELECTION" )
        count_curr = len([_row_[0] for _row_ in arcpy.da.SearchCursor(f2, ['FID'])])
        dumm = f2
        f2 = f1
        f1 = dumm
        if count_curr == count_old:
            break
        else:
            count_old = count_curr
    arcpy.CopyFeatures_management(f2, output_feature)


arcpy.MakeFeatureLayer_management(new_links_shp, linksn_f)
arcpy.MakeFeatureLayer_management(links_o, "bufferf")
arcpy.Buffer_analysis(links_o, im_t, clip_distance, "", "", "ALL", "","")
arcpy.SelectLayerByLocation_management(linksn_f, "COMPLETELY_WITHIN", im_t, "", "NEW_SELECTION")
arcpy.CopyFeatures_management(linksn_f, im_t)


extract_connected_links(im_t, links_n)



arcpy.AddField_management(links_n, "_ID_", "LONG")
arcpy.CalculateField_management(links_n, "_ID_", '!FID!', "PYTHON")

#get new nodes
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





