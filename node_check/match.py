import arcpy
import pandas


node_id = raw_input("Enter the node ID: ")
rr = raw_input("Enter the RR: ")

shp = '../../RAIL/gis/alllinks.shp'
transfers_all = "../../RAIL/transfers/intermediate/transfercsv.csv"

colname_list = ['FID', 'ID', 'RR1', 'RR2', 'RR3', 'RR4', 'RR5', 'LINK_TYPE', 'SIGNAL', 'CAPY_CODE', 'FF_SPEED', 'A_NODE', "B_NODE"]
all_rrs = ['RR1', 'RR2', 'RR3', 'RR4', 'RR5']
transfers_df = pandas.read_csv(transfers_all)


dict_= {}

#functions
node = 34012
rr = 555
def get_transfers_at_node_id(node,rr):
    list1 = transfers_df[(transfers_df.ID ==node) & (transfers_df.JRR2NO == rr)]['JRR1NO'].tolist()
    list2 = transfers_df[(transfers_df.ID ==node) & (transfers_df.JRR1NO == rr)]['JRR2NO'].tolist()
    return list(set(list1 + list2))

def get_connecting_nodes(node,rr):
    if (node,rr) in master_flow.keys():
        return master_flow[(node,rr)]
    else:
        nodes_all_rrs = df[(df.A_NODE == node) | (df.B_NODE==node) & (df.LINK_TYPE.isin([2,4]))]
        nodes_with_rrs = nodes_all_rrs[nodes_all_rrs.isin([rr])].any(axis = 1)
        df_of_nodes = nodes_all_rrs.loc[nodes_with_rrs][['A_NODE', "B_NODE"]]
        list_of_nodes = df_of_nodes.iloc[:,0].tolist() + df_of_nodes.iloc[:,1].tolist()
        list_of_nodes = [x for x in list_of_nodes if x !=node]
        list_of_nodes = [x for x in list_of_nodes if x not in all_reached_nodes] #avoid going back
        set_of_values = [(x, rr) for x in list_of_nodes]
        transfers = []
        for _node_ in list_of_nodes:
            transfers = get_transfers_at_node_id(_node_, rr)
        master_flow[(node,rr)] = set_of_values + [(node,y) for y in transfers]
        all_reached_nodes.append(node)
    return set_of_values

with arcpy.da.SearchCursor(shp, colname_list) as cursor:
    for row in cursor:
        dict_[row[0]] = row[1:]

df = pandas.DataFrame.from_dict(dict_).transpose()
df.columns = [colname_list[1:]]


node_id = 34012
rr = 555

master_flow = {}
all_reached_nodes = []


all_rrs = [rr] + get_transfers_at_node_id(node_id,rr)
node_rr_list = [(node_id, x) for x in all_rrs ]

for [x,y] in node_rr_list:
    master_flow[(x,y)] = (get_connecting_nodes(x,y))

i = 0
while True:
    print (i)
    master_flow1 = master_flow.copy()
    for (node,rr),nodes_rr_list in master_flow1.iteritems():
        #print "({0},{1})->{2}".format(node,rr, nodes_rr_list)
        for _node_,rr in nodes_rr_list:
            if _node_ in all_reached_nodes:
                continue
            transfers = get_transfers_at_node_id(_node_,rr)
            all_rrs = [rr] + transfers
            node_rr_list = [(_node_, x) for x in all_rrs]
            for [x, y] in node_rr_list:
                a = get_connecting_nodes(x, y)
    if master_flow == master_flow1:
        break
    i = i+1

for key,values in master_flow.iteritems():
    print key,values

pandas.DataFrame.from_dict(master_flow, orient = 'index').to_csv("apple.csv")

