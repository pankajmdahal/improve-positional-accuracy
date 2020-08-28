#get required shapes and validate
import arcpy
from parameters import *
import timeit


links_o = old_links_shp  # use this area to crop the new link
links_n = new_links_clipped  # cropped area would be outputted to this file
nodes_n = new_nodes_shp  # the nodes calculated from new links would be outputted here
nodes_o = old_nodes_shp  # the nodes calculated from old links would be outputted here


def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]

def remove_unconnected_links(line_feature):
    im_temp = "in_memory/ppp"
    #im_temp = "C:/GIS/temppoo.shp"
    fid = [58004, 84356]
    f1 = "fff1"
    f2 = "fff2"
    arcpy.MakeFeatureLayer_management(line_feature, f1)
    arcpy.MakeFeatureLayer_management(line_feature, f2)
    arcpy.SelectLayerByAttribute_management(f1, "NEW_SELECTION", get_where_clause("FID", fid))
    count_old = 0
    while True:
        arcpy.SelectLayerByLocation_management(f2, "INTERSECT", f1, "", "ADD_TO_SELECTION" )
        count_curr = len([_row_[0] for _row_ in arcpy.da.SearchCursor(f2, ['FID'])])
        dumm = f2
        f2 = f1
        f1 = dumm
        if count_curr == count_old:
            break
        else:
            count_old = count_curr
    arcpy.CopyFeatures_management(f2, im_temp)
    return im_temp


def get_links_in_new_network_completely_within_old_buffer(new_links, old_links):
    linksn_f = "linksf"
    im_t = "in_memory/pppp"
    arcpy.MakeFeatureLayer_management(new_links, linksn_f)
    arcpy.Buffer_analysis(old_links, im_t, old_link_buffer_clip_distance, "", "", "ALL", "", "")
    arcpy.SelectLayerByLocation_management(linksn_f, "COMPLETELY_WITHIN", im_t, "", "NEW_SELECTION")
    arcpy.CopyFeatures_management(linksn_f, im_t)
    return im_t

#get new nodes
def get_nodes_from_links(links_shp):
    im_t = "in_memory/pp"
    arcpy.FeatureVerticesToPoints_management(links_shp, im_t, "BOTH_ENDS")
    arcpy.DeleteIdentical_management(im_t, ['Shape'])
    arcpy.AddField_management(im_t, "_ID_", "LONG")
    arcpy.CalculateField_management(im_t, "_ID_", '!FID!', "PYTHON")
    fieldnames = [x for x in [f.name for f in arcpy.ListFields(im_t)] if x not in ['FID', 'Shape', 'OID', "_ID_"]]
    arcpy.DeleteField_management(im_t, fieldnames)
    return im_t


def add_unique_ids(link_shp):
    arcpy.AddField_management(link_shp, "_ID_", "LONG")
    arcpy.CalculateField_management(link_shp, "_ID_", '!FID!', "PYTHON")
    return link_shp

#you can decrease the buffer distance if you want to
im_t = get_links_in_new_network_completely_within_old_buffer(new_links_shp, links_o)
feature = remove_unconnected_links(im_t)
arcpy.CopyFeatures_management(feature, links_n)

#get new nodes
links_n = add_unique_ids(links_n)
im_t = get_nodes_from_links(links_n)
arcpy.CopyFeatures_management(im_t, nodes_n)

# get old nodes
links_o = add_unique_ids(links_o)
im_t = get_nodes_from_links(links_o)
arcpy.CopyFeatures_management(im_t, nodes_o)







