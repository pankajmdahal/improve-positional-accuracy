import arcpy
import pandas
import numpy as np
from params import *

# for each link in old link, there has to be a link in the new network within 5 miles radious with the same attributes
arcpy.env.overwriteOutput = True

new_shpf = "newshpf"

merged_links = 'input/shp/merged_links.shp'
merged_linksf = 'mergedf'



temp = "C:/GIS/temp.shp"
clipped_states_in = 'C:/GIS/clipped_in.shp'



arcpy.MakeFeatureLayer_management(merged_links, merged_linksf)
arcpy.MakeFeatureLayer_management(new_shp, new_shpf)


# functions
def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]


# gives you the id of the new link that has the specified attributes
#(old_attributes, new_node_fids) = (row, ids_list)
def get_id_with_attributes(old_attributes, nearby_link_ids):
    lists_of_nearby_links = []
    with arcpy.da.SearchCursor(new_shp, colname_list, where_clause=get_where_clause("FID", nearby_link_ids)) as cursor:
        for row in cursor: #get the FIDs of new_shp that matches nearby link ids
            if old_attributes[2:] == row[2:]:
                lists_of_nearby_links.append(row[0])
    return lists_of_nearby_links

def get_fids_within_area():
    arcpy.SelectLayerByLocation_management(merged_linksf, "INTERSECT", clipped_states_in)
    fids_list = [_row_[0] for _row_ in arcpy.da.SearchCursor(merged_linksf, ['FID'])]
    return fids_list

not_found_fids = []
fids_within_area = get_fids_within_area()
all_fids = [_row_[0] for _row_ in arcpy.da.SearchCursor(merged_links, ['FID'])]
fids_out_area = [x for x in all_fids if x not in fids_within_area]
fid_mapping = {}

with arcpy.da.SearchCursor(merged_links, colname_list, where_clause=get_where_clause("FID", fids_within_area)) as cursor:
    for row in cursor:
        where_clause = """ "FID" = %d""" % row[0]
        arcpy.SelectLayerByAttribute_management(merged_linksf, "NEW_SELECTION", where_clause)
        for search_dist in search_dist_list:
            arcpy.Buffer_analysis(merged_linksf, "in_memory/m1", str(search_dist) + " Miles")
            arcpy.SelectLayerByLocation_management(new_shpf, "COMPLETELY_WITHIN", "in_memory/m1", "", "NEW_SELECTION")
            fids_list = [_row_[0] for _row_ in arcpy.da.SearchCursor(new_shpf, ['FID'])]
            if len(fids_list) == 0:
                continue
            fids = get_id_with_attributes(row, fids_list)
            if len(fids) == 0:
                if search_dist == search_dist_list[-1]:
                    not_found_fids.append(row[1])
                else:
                    continue
            elif len(fids)>0: #its okay if FIDs were found, if not increase search_distance and search again
                print "{0}->{1},{2}".format(row[0],fids,search_dist)
                break
        fid_mapping[row[0]] =[search_dist]+ ['in'] + fids

print "Set of not found fids: ".format(set(not_found_fids))

#one on one mapping
with arcpy.da.SearchCursor(merged_links, colname_list, where_clause=get_where_clause("FID", fids_out_area)) as cursor:
    for row in cursor:
        where_clause = """ "FID" = %d""" % row[0]
        arcpy.SelectLayerByAttribute_management(merged_linksf, "NEW_SELECTION", where_clause)
        arcpy.Buffer_analysis(merged_linksf, "in_memory/m1", "5 feet")
        arcpy.SelectLayerByLocation_management(new_shpf, "COMPLETELY_WITHIN", "in_memory/m1", "", "NEW_SELECTION")
        fid = [_row_[0] for _row_ in arcpy.da.SearchCursor(new_shpf, ['FID'])]
        fid_mapping[row[0]] =[0]+ ['out'] + fid
        print "{0}->{1},{2}".format(row[0], fid, [0])


dict_df = pandas.DataFrame({ key:pandas.Series(value) for key, value in fid_mapping.items()}).transpose()
dict_df.to_csv("fidmapping.csv")

arcpy.CopyFeatures_management(merged_links, final_output)
