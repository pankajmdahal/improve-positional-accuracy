import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random

threshold = 1

all_dict = np.load("./intermediate/link_route_type_dict.npy", allow_pickle=True, encoding='latin1').item()

all_df = pd.DataFrame(all_dict).transpose().reset_index()
all_df.columns = ['LINK_ID', "ORIG_LENG", "ROUTE_LENG", "Type"]
all_df['Tolerance'] = all_df.apply(lambda x: abs(x['ROUTE_LENG'] - x['ORIG_LENG']) / (x['ORIG_LENG']), axis=1)




df_= all_df[['Type','Tolerance']]
#df_ = df_[df_.Tolerance <=0.999]
_df_ = df_.sort_values(by='Tolerance', ascending=False).reset_index()[['Type', 'Tolerance']].reset_index()
_df_ = _df_.head(100)

# df_1.plot(x='index', y='TOL', kind='line', figsize=(10, 8), legend=False, style='mo-', hue = "TYPE")
# plt.show()

#scatterplot
plt.scatter(_df_.index.to_list(),_df_.Tolerance.to_list(),alpha = 1, edgecolor = 'none', s=3)
plt.title('Tolerance vs index (combined)')
plt.xlabel('Index')
plt.ylabel('Tolerance')
plt.show()
sns.scatterplot(data=_df_, x='index', y='Tolerance', hue='Type', palette=['black', 'grey'])
plt.show()



#independent plots
df_2= all_df[all_df.Type ==2][['Type','Tolerance']]
df_3= all_df[all_df.Type ==3][['Type','Tolerance']]

# df_2 = df_1[df_2.Tolerance <=0.999]
# df_3 = df_2[df_3.Tolerance <=0.999]

_df_3 = df_3.sort_values(by='Tolerance', ascending=False).reset_index()[['Type', 'Tolerance']].reset_index()
_df_2 = df_2.sort_values(by='Tolerance', ascending=False).reset_index()[['Type', 'Tolerance']].reset_index()


_df_1 = _df_3.head(500)
_df_2 = _df_2.head(500)

# df_1.plot(x='index', y='TOL', kind='line', figsize=(10, 8), legend=False, style='mo-', hue = "TYPE")
# plt.show()


p1 = plt.scatter(_df_1.index.to_list(),_df_1.Tolerance.to_list(),alpha = 1, color = 'blue', s=3)
p2 = plt.scatter(_df_2.index.to_list(),_df_2.Tolerance.to_list(),alpha = 1, color = 'red', s=3)
xs = np.linspace(1, 50, 500)
p3 = plt.hlines(y=1, xmin=0, xmax=len(xs), colors='g', linestyles='--', lw=1)
plt.title('Tolerance vs index (combined)')
plt.xlabel('Index')
plt.ylabel('Tolerance')
plt.legend((p1,p2, p3), ("Route found outside buffer", "Route found inside buffer", "threshold = 1"))
#plt.axhline(y=0.1, color='g', linestyle='-')

plt.show()




#pool both plot

x1 = df_3['Tolerance'].tolist()
x2 = df_2['Tolerance'].tolist()

#x1 = [x for x in x1 if x<30]

plt.figure()
n_bins=20
labels = ['Route found out of buffer', 'Route found out of buffer']
plt.legend(loc="upper right")
colors= ["blue", "red"]
plt.xlabel("Threshold")
plt.ylabel("Number of links found")
plt.title("Number of links found vs Threshold")

from matplotlib.patches import Rectangle

handles = [Rectangle((0,0),1,1,color=c,ec="k") for c in colors]
labels = ['Route found inside buffer', 'Route found out of buffer']
plt.legend(handles, labels)


plt.hist([x1,x2], n_bins, log=True, color = colors, rwidth = 0.9, stacked =True)
plt.show()




# id_min_dist_df = pd.read_csv("id_min_dist.csv")
# ids_dist_list = id_min_dist_df['Min distance to any link: '].tolist()
#
# ids_dist_list = [x for x in ids_dist_list if x>0]
#
# plt.figure()
# n_bins=30
#
#
# plt.xlabel("Buffer distance (miles)")
# plt.ylabel("Number of links found")
# plt.title("Number of links found vs buffer distance")
#
# bin = [10,30,50,70,90,110,130,150,170,190,210,230,250,270,290,310,330,350,370,390,410, 430]
#
# plt.hist(ids_dist_list, bins = bin, color = 'grey', log=True, rwidth = 0.9)
# plt.show()

