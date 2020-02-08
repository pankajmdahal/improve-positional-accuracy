import arcpy

arcpy.env.overwriteOutput = True

buffer_dist = 100 #ft distance where the links like
search_dist = 2 #miles distance to where the new links has to be found
snap_dist = 5280 #ft (validated distance)


#clip_state_list = ["'TN'", "'NC'","'SC'","'GA'","'FL'","'AL'","'MS'"]
clip_state_list = ["'FL'"]
colname_list = ['FID','ID','RR1', 'RR2','RR3','RR4', 'RR5', 'LINK_TYPE', 'SIGNAL', 'CAPY_CODE', 'FF_SPEED']

new_shp = 'input/shp/alllinks.shp'
old_shp = 'input/shp/old_links.shp'
all_states = 'input/shp/tl_2017_us_states.shp'
final = "input/shp/joined.shp"
empty = "C:/GIS/empty.shp"
connecting_lines_at_border = "C:/GIS/clab.shp"
connecting_lines_at_border_f = "clabf"

alllinks = 'input/shp/merged_links.shp'
alllinks_f = "alllinksf"

disk_shp = 'C:/GIS/dumm.shp'



clipped_old = 'C:/GIS/c1.shp'
clipped_new = 'C:/GIS/c2.shp'

clipped_new_pt = 'C:/GIS/cp1.shp'
clipped_old_pt = 'C:/GIS/cp2.shp'


temp = "C:/GIS/temp.shp"
temp1 = "C:/GIS/temp1.shp"

m = "C:/GIS/m.shp"
m_line = "C:/GIS/ml.shp"

# clipped_old = 'in_memory/c1'
# clipped_new = 'in_memory/c2'

clipped_states_in = 'C:/GIS/clipped_in.shp'
clipped_states_out = 'C:/GIS/clipped_out.shp'

all_states_f = "allstatesf"
new_shpf = "newshpf"
clipped_old_f = "co"
clipped_new_f = "cn"

clipped_old_pt_f = 'cpo'
clipped_new_pt_f = 'cpn'

m_line_f = "mlf"

arcpy.CopyFeatures_management(empty,connecting_lines_at_border)


#functions
def get_where_clause(colname, list_of_link_ids):
    wh_cl = ""
    for id in list_of_link_ids:
        wh_cl = wh_cl + """"{0}" = {1} OR """.format(colname, id)
    return wh_cl[:-4]

def get_id_with_attributes(old_attributes, new_node_fids): #gives you the id of the new link that has the specified attributes
    lists_of_nearby_links = []
    print old_attributes
    with arcpy.da.SearchCursor(clipped_new_pt, colname_list, where_clause=get_where_clause("FID", new_node_fids)) as cursor:
        for row in cursor:
            print row
            if old_attributes[2:] == row[2:]:
                lists_of_nearby_links.append(row[0])
    return lists_of_nearby_links


#preparing clip
arcpy.MakeFeatureLayer_management(all_states, all_states_f)
where_clause = get_where_clause("Abbr", clip_state_list)



#clip old
arcpy.SelectLayerByAttribute_management(all_states_f, "NEW_SELECTION", where_clause)
arcpy.CopyFeatures_management(all_states_f, clipped_states_in)
arcpy.Clip_analysis(old_shp,clipped_states_in,clipped_old) #in,clip,out



#clip_new
arcpy.SelectLayerByAttribute_management(all_states_f, "SWITCH_SELECTION", where_clause)
arcpy.CopyFeatures_management(all_states_f, clipped_states_out)
arcpy.Clip_analysis(new_shp,clipped_states_out,clipped_new) #in,clip,out



#get end points
arcpy.FeatureVerticesToPoints_management(clipped_new, temp, "BOTH_ENDS")
arcpy.MakeFeatureLayer_management(temp, "temp")
arcpy.SelectLayerByLocation_management("temp", "INTERSECT", clipped_states_in)
arcpy.CopyFeatures_management("temp",clipped_new_pt)

arcpy.FeatureVerticesToPoints_management(clipped_old, temp, "BOTH_ENDS")
arcpy.MakeFeatureLayer_management(temp, "temp")
arcpy.SelectLayerByLocation_management("temp", "INTERSECT", clipped_states_out)
arcpy.CopyFeatures_management("temp",clipped_old_pt)


arcpy.MakeFeatureLayer_management(clipped_old_pt, clipped_old_pt_f)
arcpy.MakeFeatureLayer_management(clipped_new_pt, clipped_new_pt_f)


arcpy.MakeFeatureLayer_management(clipped_old, clipped_old_f)
arcpy.MakeFeatureLayer_management(clipped_new, clipped_new_f)


#cut features should not be multipart
#add this later


#now the most important part comes by
arcpy.Buffer_analysis(clipped_old_pt_f,temp,str(buffer_dist) + " feet")
arcpy.SelectLayerByLocation_management(clipped_old_pt_f, "INTERSECT", temp)

old_id_list = list(set([row[0] for row in arcpy.da.SearchCursor(clipped_old_pt_f, ['ID'])]))

print old_id_list[0]
not_snapped_ids = []
multipart = []



with arcpy.da.SearchCursor(clipped_old_pt, colname_list, where_clause=get_where_clause("ID", old_id_list)) as cursor:
    for row in cursor:
        print "Working on ID: {0}".format(row[1])
        where_clause = """ "ID" = %d""" % row[1]
        arcpy.SelectLayerByAttribute_management(clipped_old_pt_f,"NEW_SELECTION", where_clause)
        number_of_cuts = len([_row_[0] for _row_ in arcpy.da.SearchCursor(clipped_old_pt_f, ['ID'])])
        if number_of_cuts !=1:
            multipart.append(row[1])
            print ("out1*******************************************")
            continue
        arcpy.SelectLayerByLocation_management(clipped_new_pt_f, "WITHIN_A_DISTANCE", clipped_old_pt_f, str(search_dist) + " Mile","NEW_SELECTION")
        #the nodes cant be selected using ids, since it has two, so fid used
        new_fid_list = [_row_[0] for _row_ in arcpy.da.SearchCursor(clipped_new_pt_f, ['FID'])]
        print new_fid_list
        fid = get_id_with_attributes(row, new_fid_list)
        print ("Nearby FIDs with matches: {0}".format(fid))
        if len(fid) !=1:
            not_snapped_ids.append(row[1])
            print ('out2*******************************************')
            continue
        else:
            print ("Logging...")
            where_clause = get_where_clause("FID", fid)
            arcpy.SelectLayerByAttribute_management(clipped_new_pt_f, "NEW_SELECTION", where_clause)
            new_fid_list = [_row_[0] for _row_ in arcpy.da.SearchCursor(clipped_new_pt_f, ['FID'])]
            arcpy.Merge_management([clipped_new_pt_f,clipped_old_pt_f],m)
            arcpy.PointsToLine_management(m, m_line)


            #combine the small segment with old and new links to form a single line
            arcpy.MakeFeatureLayer_management(m_line, m_line_f)
            arcpy.SelectLayerByLocation_management(clipped_old_f, "INTERSECT", m_line_f, "","NEW_SELECTION")
            arcpy.SelectLayerByLocation_management(clipped_new_f, "INTERSECT", m_line_f, "","NEW_SELECTION")
            arcpy.Merge_management([m_line_f,clipped_old_f, clipped_new_f], temp)
            arcpy.Dissolve_management(temp, m_line, "", "", "SINGLE_PART", "DISSOLVE_LINES")

            #get the attributes
            [arcpy.AddField_management(m_line, x, "SHORT", "", "", "", "", "NON_NULLABLE", "NON_REQUIRED", "") for x in colname_list[2:]]
            with arcpy.da.UpdateCursor(m_line, colname_list[1:]) as _cursor_:
                for _row_ in _cursor_:
                    _row_ = row[1:]
                    _cursor_.updateRow(_row_)
            #delete from others
            arcpy.DeleteFeatures_management(clipped_old_f)
            arcpy.DeleteFeatures_management(clipped_new_f)

            arcpy.Merge_management([m_line, connecting_lines_at_border], temp)
            arcpy.Copy_management(temp, connecting_lines_at_border)



#blah blah blah blah (snapping)
arcpy.FeatureVerticesToPoints_management (clipped_old, disk_shp, "BOTH_ENDS")
arcpy.Snap_edit(disk_shp, [[disk_shp, "END", "100 Feet"]])
arcpy.Snap_edit(clipped_old, [[disk_shp, "END", "100 Feet"]])

arcpy.FeatureVerticesToPoints_management (clipped_new, disk_shp, "BOTH_ENDS")
arcpy.Snap_edit(disk_shp, [[disk_shp, "END", "10 Feet"]])
arcpy.Snap_edit(clipped_new, [[disk_shp, "END", "5 Feet"]])


arcpy.Merge_management([clipped_new,clipped_old,connecting_lines_at_border], alllinks )


print "Different Attributes, or multipart on new: {0}".format(list(set(not_snapped_ids)))
print "Multipart on old: {0}".format(list(set(multipart)))


#one on one matching
