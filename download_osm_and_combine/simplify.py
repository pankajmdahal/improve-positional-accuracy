#simplyfing the final map
import arcpy

arcpy.env.overwriteOutput = True

#final_shp = "./output/highway_ln.shp"
final_shp= "./intermediate/shapefiles/tennessee/road_cropped.shp"
final_shp_f = "finalshp"

final_shp1 = "./output/highway_ln1.shp"
final_shp1f = "in_memory/S1"

buffer_dist = 2 #feet
temp = "C:/GIS/temp.shp" #since the memory cant hold everything
temp1 = "C:/GIS/temp12.shp"
temp_f = "tempf"
temp2 = "C:/GIS/apple.shp"



def get_new_links(list_of_links):
    _list_ = []
    for link in list_of_links:
        _list_.extend(fid_fid_dict[link])
    return list(set(_list_))


arcpy.CopyFeatures_management(final_shp,temp)
#creating a copy
try:
    arcpy.AddField_management(temp, "length", "FLOAT")
    arcpy.CalculateField_management(temp, "length", '!Shape.length@miles!', "PYTHON")
except:
    print ("length already present")


arcpy.CopyFeatures_management(temp,temp1)
arcpy.MakeFeatureLayer_management(temp,"temp")
arcpy.MakeFeatureLayer_management(temp1,"temp1")


#creating a dict of link with its connected links
fid_fid_dict = {}
with arcpy.da.SearchCursor(temp, ["FID"]) as curs:
    for row in curs:
        arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", '"FID" = {}'.format(row[0]))
        arcpy.SelectLayerByLocation_management('temp1', "INTERSECT", "temp", "", "NEW_SELECTION")
        fid_fid_dict[row[0]] = [_row_[0] for _row_ in arcpy.da.SearchCursor("temp1", ['FID'])]


#get disconnected nodes
to_search = [100]
previous_links = []
searched_links = []
count = 0
while True:
    new_links = get_new_links(to_search)
    new_not_in_searched = [x for x in to_search if x not in searched_links]
    searched_links.extend(new_not_in_searched)
    to_search = [x for x in new_links if x not in searched_links]
    if len(to_search)==0:
        break

not_found = [str(x) for x in fid_fid_dict if x not in searched_links]
print not_found
#delete features that are not touching

field_str = ", ".join(not_found)
where_clause = "FID NOT IN ({})".format(field_str)
arcpy.SelectLayerByAttribute_management("temp","NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management("temp", final_shp1)
print "Unconnected nodes removed."

#preparing data
arcpy.Buffer_analysis(final_shp1,temp,str(buffer_dist) + " feet")
arcpy.MakeFeatureLayer_management(temp,temp_f)
arcpy.MakeFeatureLayer_management(final_shp,final_shp_f)

#add columns
try:
    arcpy.AddField_management(final_shp1,"length", "FLOAT")
    arcpy.CalculateField_management(final_shp1, "length", '!Shape.length@miles!', "PYTHON")
except:
    pass
try:
    arcpy.AddField_management(final_shp1,"speed", "FLOAT")
except:
    pass
try:
    arcpy.AddField_management(final_shp1,"resist", "FLOAT")
except:
    pass

#getting speed for each link
with arcpy.da.UpdateCursor (final_shp1, ["FID", "speed"]) as curs:
    for row in curs:
        where_clause = """ "FID" = %d""" % row[0]
        #arcpy.Select_analysis(temp, temp_f, where_clause)
        arcpy.SelectLayerByAttribute_management(temp_f,"NEW_SELECTION", where_clause) #select a buffer
        #most of the cases are covered by this
        arcpy.SelectLayerByLocation_management(final_shp_f, "COMPLETELY_WITHIN", temp_f)
        fid_speed_len_dict1 = {_row_[0]: [_row_[1], _row_[2]] for _row_ in arcpy.da.SearchCursor(final_shp_f, ['FID','speed', 'length'])}
        if not fid_speed_len_dict1: #if the dict is empty,
            arcpy.Clip_analysis(final_shp,temp_f,temp2) #in,clip,out
            fid_speed_len_dict = {_row_[0]: [_row_[1],_row_[2]] for _row_ in arcpy.da.SearchCursor(temp2, ['FID','speed', "SHAPE@LENGTH"])}
            fid_speed_len_dict1 = {a:[b,c] for a,[b,c] in fid_speed_len_dict.iteritems() if c > float(buffer_dist)/5280*1.5}
        if not fid_speed_len_dict1: #if the lengths are less than buffer distance, the speed would be maximum of all the speeds
            row[1] = max([b for a,[b,c] in fid_speed_len_dict.iteritems()])
            curs.updateRow(row)
            continue
        length_list = [y for x,y in fid_speed_len_dict1.values()]
        length_to_speed_list = [float(y[1])/float(y[0]) for x,y in fid_speed_len_dict1.iteritems()]
        row[1] = int(sum(length_list)/sum(length_to_speed_list)) #float speed doesnot make any sense
        curs.updateRow(row)

arcpy.CalculateField_management(final_shp1, "resist", '!length!/!speed!', "PYTHON")