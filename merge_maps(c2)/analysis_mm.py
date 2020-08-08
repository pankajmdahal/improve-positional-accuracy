import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random

threshold = 1

no_routes = pd.read_csv("csv/noroutes.csv")
no_tolerance = pd.read_csv("csv/notolerance.csv")
no_tolerance_buffer = pd.read_csv("csv/notolerancebuffer.csv")

no_tolerance['Type'] = 'Route found out of buffer'
no_tolerance_buffer['Type'] = 'Route found within buffer'

combined = no_tolerance.append(no_tolerance_buffer)

combined.columns = ['LINK_ID', "ROUTE_LENG", "ORIG_LENG", "Type"]


combined['Tolerance'] = combined.apply(lambda x: abs(x['ROUTE_LENG'] - x['ORIG_LENG']) / (x['ORIG_LENG']), axis=1)


df_= combined[['Type','Tolerance']]
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




categorical_values = pd.cut(df_.Tolerance, [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
counts = pd.value_counts(categorical_values)
counts.plot.hist()
plt.show()




#independent plots

no_tolerance['Type'] = 'Route found out of buffer'
no_tolerance_buffer['Type'] = 'Route found within buffer'

combined1 = no_tolerance
combined2 = no_tolerance_buffer

combined1.columns = ['LINK_ID', "ROUTE_LENG", "ORIG_LENG", "Type"]
combined2.columns = ['LINK_ID', "ROUTE_LENG", "ORIG_LENG", "Type"]


combined1['Tolerance'] = combined1.apply(lambda x: abs(x['ROUTE_LENG'] - x['ORIG_LENG']) / (x['ORIG_LENG']), axis=1)
combined2['Tolerance'] = combined2.apply(lambda x: abs(x['ROUTE_LENG'] - x['ORIG_LENG']) / (x['ORIG_LENG']), axis=1)

#anything greater than 5 would be 5

df_1 = df


df_1= combined1[['Type','Tolerance']]
df_2= combined2[['Type','Tolerance']]
# df_1 = df_1[df_1.Tolerance <=0.999]
# df_2 = df_2[df_2.Tolerance <=0.999]

_df_1 = df_1.sort_values(by='Tolerance', ascending=False).reset_index()[['Type', 'Tolerance']].reset_index()
_df_2 = df_2.sort_values(by='Tolerance', ascending=False).reset_index()[['Type', 'Tolerance']].reset_index()

_df_1 = _df_1.head(500)
_df_2 = _df_2.head(500)

# df_1.plot(x='index', y='TOL', kind='line', figsize=(10, 8), legend=False, style='mo-', hue = "TYPE")
# plt.show()


p1 = plt.scatter(_df_1.index.to_list(),_df_1.Tolerance.to_list(),alpha = 1, color = 'blue', s=3)
p2 = plt.scatter(_df_2.index.to_list(),_df_2.Tolerance.to_list(),alpha = 1, color = 'red', s=3)
xs = np.linspace(1, 50, 500)
p3 = plt.hlines(y=0.1, xmin=0, xmax=len(xs), colors='g', linestyles='--', lw=1)
plt.title('Tolerance vs index (combined)')
plt.xlabel('Index')
plt.ylabel('Tolerance')
plt.legend((p1,p2, p3), ("Route found outside buffer", "Route found inside buffer", "threshold = 0.1"))
#plt.axhline(y=0.1, color='g', linestyle='-')

plt.show()

#pool both plot

data= [math.log(x) for x in combined['Tolerance'].tolist()]

bins = np.arange(min(data)-2, max(data)+2, 1) # fixed bin size

plt.xlim([min(data)-2, max(data)+2])

plt.hist(data, bins=bins, alpha=0.5)
plt.title('Random Gaussian data (fixed bin size)')
plt.xlabel('variable X (bin size = 5)')
plt.ylabel('count')

plt.show()