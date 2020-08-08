import arcpy
import matplotlib.pyplot as plt
from multiprocessing import Pool
from time import sleep
import pandas as pd

arcpy.env.overwriteOutput = True

# shapefiles
other_pt = "./intermediate/pt_NARN_LINE_03162018.shp"
base = "./intermediate/railway_ln_connected.shp"
other_pt_f = "otherf"
base_f = "basef"
arcpy.MakeFeatureLayer_management(other_pt, other_pt_f)
arcpy.MakeFeatureLayer_management(base, base_f)


buffer_ = "in_memory/b1"
buffer_f = "bf"


dist_count_dict = {}

dist_list = range(20,420,20)
#dist_list = range(5,20,5)


# def get_dist_count(_dist_):
#     print _dist_
#     buffer_dist = str(_dist_)+" feet"
#     arcpy.Buffer_analysis(other_f, buffer_, buffer_dist, "FULL", "ROUND", "ALL")
#     arcpy.MakeFeatureLayer_management(buffer_, buffer_f)
#     arcpy.SelectLayerByLocation_management(base_f, 'INTERSECT', buffer_f, '', "NEW_SELECTION")
#     count = int(arcpy.GetCount_management(base_f)[0])
#     return count

list_of_all_node_ids = [_row_[0] for _row_ in arcpy.da.SearchCursor(other_pt, ['_ID_'])]


def get_dist_count1(_id_):
    print _id_
    for _dist_ in dist_list:
        where_clause = """ "_ID_" = %d""" % _id_
        arcpy.SelectLayerByAttribute_management(other_pt_f, "NEW_SELECTION", where_clause)
        buffer_dist = str(_dist_)+" feet"
        arcpy.Buffer_analysis(other_pt_f, buffer_, buffer_dist, "FULL", "ROUND", "ALL")
        arcpy.SelectLayerByLocation_management(base_f, 'INTERSECT', buffer_, '', "NEW_SELECTION")
        count = int(arcpy.GetCount_management(base_f)[0])
        if count >0:
            link_ids = [_row_[0] for _row_ in arcpy.da.SearchCursor(base_f, ['_ID_'])]
            return _dist_,link_ids
    return -99, []



def main():
    p = Pool()
    min_dist_list = p.map(get_dist_count1, list_of_all_node_ids)
    p.close()
    p.join()
    dist_list = [x for (x,y) in min_dist_list ]
    list_of_list_of_links = [y for (x,y) in min_dist_list ]
    df = pd.DataFrame({"IDs: ":list_of_all_node_ids, "Min distance to any link: ": dist_list, "IDs of Links": list_of_list_of_links})
    #df.to_csv("dist_v_no_of_links.csv")
    df.to_csv("id_min_dist.csv")

if __name__ == '__main__':
    main()





