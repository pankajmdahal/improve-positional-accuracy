#this python script finds the important links using the commodity file
#the input link should already be dissolved and feature to line


import arcpy
import pandas
import numpy

arcpy.env.overwriteOutput = True


alllinks = "../shp/railway_ln_connected/railway_ln_connected.shp"
alllinks_f= "feature" #in_memory doesnot work
feature = "C:/GIS/deletethis1.shp" #can use in_memory
ND ="../shp/railway_ln_connected/railway_ln_connected_ND.nd"

fips = "C:/Users/pankaj/Desktop/RAIL/gis/standards/FIPS.shp"
snapped_fips = "C:/GIS/deletethis.shp"
o = "C:/GIS/o.shp"  # temporary files
d = "C:/GIS/d.shp"
m = "C:/GIS/m.shp"

link_ID_count_flow_dict = {}
unknown_routes_dict = {}

#base commodity file
OD = "C:/Users/pankaj/Desktop/RAIL/input/base/base.xlsx"
od_df = pandas.ExcelFile(OD).parse("Sheet1")

def get_shortest_path_link_ids(fips_a, fips_b):
    #print ("ArgGIS analyst: Job Received, OFIPS: {0}, DFIPS: {1} *".format(fips_a, fips_b))
    arcpy.CheckOutExtension("Network")
    arcpy.Select_analysis(snapped_fips, o, 'FIPS = {0}'.format(fips_a))
    arcpy.Select_analysis(snapped_fips, d, 'FIPS = {0}'.format(fips_b))
    arcpy.Merge_management([o, d], m)
    arcpy.AddLocations_na("Route", "Stops", m, "Name Name #", "5000 Kilometers", "",
                          "B1 SHAPE;B1_ND_Junctions SHAPE",
                          "MATCH_TO_CLOSEST", "CLEAR", "NO_SNAP", "5 Meters", "INCLUDE", "B1 #;B1_ND_Junctions #")
    try:
        arcpy.Solve_na("Route", "SKIP", "TERMINATE", "500 Kilometers")
        arcpy.SelectData_management("Route", "Routes")
        arcpy.FeatureToLine_management("Route/Routes", feature, "", "ATTRIBUTES")
    except:
         print ("Route between FIPS: {0} and {1} not found.".format(fips_a,fips_b))
         unknown_routes_dict[fips_a]=fips_b
         return []
    arcpy.SelectLayerByLocation_management(alllinks_f,"INTERSECT",feature, "", "NEW_SELECTION", "NOT_INVERT")
    dummy = [row.getValue("OBJECTID") for row in arcpy.SearchCursor(alllinks_f)]
    return dummy

def update_ids_quantity(ids,quantity):
   for id in ids:
       if id in link_ID_count_flow_dict.keys():
           link_ID_count_flow_dict[id][0] =  link_ID_count_flow_dict[id][0]+1
           link_ID_count_flow_dict[id][1] = link_ID_count_flow_dict[id][1] + quantity
       else:
           link_ID_count_flow_dict[id]=[1,quantity]


#step0:make featureclass
arcpy.MakeRouteLayer_na(ND, "Route", "Length")
arcpy.MakeFeatureLayer_management(alllinks,alllinks_f)


#step1, snap all fips to the links (preprocessing that maybe required: delete the links not connected to the network)
arcpy.Copy_management(fips, snapped_fips)
arcpy.Snap_edit(snapped_fips, [[alllinks, "EDGE", "100 Miles"]])


od_df_pivot = pandas.pivot_table(od_df, values='XTON', index=['OFIP', 'TFIP'], aggfunc=numpy.sum)
od_df_pivot = od_df_pivot.reset_index()

for i in range(len(od_df_pivot)):
    ofip = od_df_pivot.iloc[[i]]['OFIP'].tolist()[0]
    tfip = od_df_pivot.iloc[[i]]['TFIP'].tolist()[0]
    qty = od_df_pivot.iloc[[i]]['XTON'].tolist()[0]
    ids = get_shortest_path_link_ids(ofip, tfip)
    update_ids_quantity(ids,qty)
    if i%500 == 0:
        # write these values to a file for backup
        df1 = pandas.DataFrame(link_ID_count_flow_dict).transpose()
        df1.to_csv("links_with_qty.csv")
        df2 = pandas.DataFrame(unknown_routes_dict).transpose()
        df2.to_csv("unknown_routes.csv")

# #write these values to a file for backup
# df1 = pandas.DataFrame(link_ID_count_flow_dict).transpose()
# df1.to_csv("links_with_qty.csv")
# df2 = pandas.DataFrame(unknown_routes_dict).transpose()
# df2.to_csv("unknown_routes.csv")





