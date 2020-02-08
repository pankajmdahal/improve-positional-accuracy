#make comparable adfs
import pandas
import arcpy
import numpy as np

#adf with the changed network
adf1 = "adfs/1.ADF" #scenario



#to fid to id
shp1 = "../../RAIL11/RAIL/gis/alllinks.shp" #RAIL11
shp2 = "../../RAIL/gis/alllinks.shp" #RAIL

csv_file = "../cut_and_replace_by_old/fidmapping.csv"

#conversion
conv_df = pandas.read_csv(csv_file)
conv_df = conv_df[['1', '2', '3']].reset_index()

arcpy.env.overwriteOutput = True  # overwrite files if already present

shp1_dict = {row.getValue("FID"): row.getValue("ID") for row in arcpy.SearchCursor(shp1)} #RAIL1
shp2_dict = {row.getValue("FID"): row.getValue("ID") for row in arcpy.SearchCursor(shp2)} #RAIL

#functions
not_found_links = []

def get_flows(ids, flow):
    if ids != ids:
        ids = []
    for id in ids:
        if id in flow_dict.keys():
            flow_dict[id] = (flow + flow_dict[id])/2
        else:
            flow_dict[id] = flow





def create_new_adf_from_adf(location):
    commodity_df = pandas.read_csv(location)
    commodity_df.columns = ["ID", "Arc", "DIR", "Comm", "RR", "NetTons", "X", "Delay", "traveltime", "length", "payload"]
    commodity_df['GrossTons'] = commodity_df['NetTons'] * commodity_df['X']
    #commodity_df = commodity_df[commodity_df["RR"].isin(railroad_list) & commodity_df["Comm"].isin(commodity_list)]
    commodity_table = pandas.pivot_table(commodity_df, values='GrossTons', index=['ID'], aggfunc=np.sum).reset_index()
    commodity_table['ID'] = commodity_table['ID'].map(conv_dict)
    commodity_table.apply(lambda x: get_flows(x['ID'], x['GrossTons']),axis = 1)
    df = pandas.DataFrame.from_dict(flow_dict, orient = 'index')
    df.to_csv("apple.adf")


#for those links, assume that they have the same flow
flow_dict = {}

conv_df['index'] = conv_df['index'].map(shp2_dict)
conv_df['2'] = conv_df['2'].map(shp1_dict)
conv_df['3'] = conv_df['3'].map(shp1_dict)


conv_df = conv_df[['index','2', '3']]


conv_dict = conv_df.transpose().to_dict()
conv_dict = {y['index']:[ y['2'], y['3']] for x,y in conv_dict.iteritems()}
conv_dict = {x:[_y_ for _y_ in y if ~np.isnan(_y_)] for x,y in conv_dict.iteritems()}

create_new_adf_from_adf(adf1)




