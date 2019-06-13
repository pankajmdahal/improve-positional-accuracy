from collections import defaultdict
import arcpy
from heapq import *
import pandas as pd
import sys


sys.setrecursionlimit(10000)

def dijkstra(edges, f, t):
    g = defaultdict(list)
    for l,r,c in edges:
        g[l].append((c,r))
    q, seen, mins = [(0,f,())], set(), {f: 0}
    while q:
        (cost,v1,path) = heappop(q)
        if v1 not in seen:
            seen.add(v1)
            path = (v1, path)
            if v1 == t: return (cost, path)
            #if v1 == t: return path
            for c, v2 in g.get(v1, ()):
                if v2 in seen: continue
                prev = mins.get(v2, None)
                next = cost + c
                if prev is None or next < prev:
                    mins[v2] = next
                    heappush(q, (next, v2, path))
    return float("inf")

def remove_nests(l):
    nodes.append(l[0])
    if l[1] != ():
        remove_nests(l[1])

def pair(nodes):
    paired_nodes = []
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i==j-1:
                paired_nodes.append((nodes[i],nodes[j]))
    return paired_nodes


#returns the link with minimum resistance
def getlink(x,y):
    new = df[((df[anode]==x) & (df[bnode]==y)) | ((df[anode]==y) & (df[bnode]==x)) ]
    if len(new)!=1:
        dfnew = new.sort_values(by=resistance, ascending=True)
        return dfnew.iloc[0][id]
    else:
        return int(new[id])



link_shp = "C:/Users/pankaj/Desktop/Tools/shp/railway_ln_connected/railway_ln_connected.shp"
resistance = "Shape_Leng"
anode = "ANODE"
bnode = "BNODE"
id = "OBJECTID"
cum_field_name = "CUM_quant"

#shapefile to dataframe
#change it to a dataframe and remove the nodes whose occurances are >1
arr = arcpy.da.TableToNumPyArray(link_shp, [id,anode, bnode,resistance])
df = pd.DataFrame(arr)
df[cum_field_name] = 0
edges = []

#creating a list of sets with (anode, bnode, resistance)
for i in range(len(df)):
    edges.append((df.iloc[i][anode],df.iloc[i][bnode],df.iloc[i][resistance]))
    edges.append((df.iloc[i][bnode], df.iloc[i][anode], df.iloc[i][resistance]))

print "=== DIJKSTRA'S ALGORITHM ==="
od_df = pd.read_csv("od.csv")
od_a = "ANODE"
od_b = "BNODE"
od_r = "RESISTANCE"
od_df.columns = [[od_a, od_b, od_r]]

#FIPS converted to NODES
FIPS = "C:/Users/pankaj/Desktop/RAIL/gis/standards/FIPS.shp"
point = "C:/GIS/points.shp"
arcpy.Near_analysis(FIPS,point)

fips_to_nearfid = {row.getValue("FIPS"): row.getValue("NEAR_FID") for row in arcpy.SearchCursor(FIPS)}
near_fid_to_id = {row.getValue("FID"): row.getValue("Id") for row in arcpy.SearchCursor(point)}


fips_to_near_nodes = {x:near_fid_to_id[y] for x,y in fips_to_nearfid.iteritems()}



route_not_found_list = []
for i in range(len(od_df)):
    print("Row: {0}".format(i))
    #run dijkstra in all nodes
    a_node = fips_to_near_nodes[od_df.iloc[i][od_a]]
    b_node = fips_to_near_nodes[od_df.iloc[i][od_b]]
    quantity = od_df.iloc[i][od_r]
    nodes=[]
    result= dijkstra(edges, a_node, b_node)
    if result == float("inf"):
        print("Route not found: {0}->{1}".format(a_node,b_node))
        route_not_found_list.append(i)
        continue
    resistance_value = result[0] #total resistance (length), not used later
    list_str = str(result[1])
    list_str = list_str.replace('(','').replace(')','')
    nodes=list(eval(list_str))
    paired_nodes = pair(nodes)
    links= []
    for (a,b) in paired_nodes:
        #print("getlink({0},{1})".format(a,b))
        links.append(getlink(a,b))
    #get anode bnode from od file
    for link in links:
        df.loc[df[id] == link, cum_field_name] = df[cum_field_name] + quantity
    if(i%1000 ==0):
        df.to_csv("output.csv")


df.to_csv("output.csv")
print route_not_found_list