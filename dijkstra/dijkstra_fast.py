from collections import defaultdict
from heapq import *
import pandas

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
    new = df[((df.A_NODE==x) & (df.B_NODE==y)) | ((df.A_NODE==y) & (df.B_NODE==x)) ]
    if len(new)!=1:
        dfnew = df.sort_values(by='RESISTANCE', ascending=True)
        return dfnew.iloc[0]["ID"]
    else:
        return int(new['ID'])


if __name__ == "__main__":
    df = pandas.read_csv("network.csv")
    df["CUM_quant"] = 0
    edges = []

    #remove the edges that connects the same two nodes but with different resistance
    #to add

    for i in range(len(df)):
        edges.append((df.iloc[i]["A_NODE"],df.iloc[i]["B_NODE"],df.iloc[i]["RESISTANCE"]))
        edges.append((df.iloc[i]["B_NODE"], df.iloc[i]["A_NODE"], df.iloc[i]["RESISTANCE"]))

    print "=== Dijkstra ==="
    OD = "C:/Users/pankaj/Desktop/RAIL/input/base/base.xlsx"
    od_df = pandas.read_csv("od.csv")

    for i in range(len(od_df)):
    #run dijkstra in all nodes
        print (i)
        anode = od_df.iloc[i]["ONode"]
        bnode = od_df.iloc[i]["DNode"]
        quantity = od_df.iloc[i]["quantity"]
        nodes=[]
        result= dijkstra(edges, anode, bnode)
        resistance = result[0]
        remove_nests(result[1])
        paired_nodes = pair(nodes)
        links= []
        for (a,b) in paired_nodes:
            links.append(getlink(a,b))
        #get anode bnode from od file
        for link in links:
            df.loc[df['ID'] == link, "CUM_quant"] = df.CUM_quant + quantity
        if(i%1000 ==0):
            df.to_csv("output.csv")