import arcpy
import pandas
import matplotlib.pyplot as plt

df_ = pandas.read_csv("bufferdist_nodecount.csv").reset_index()
df_ = df_.groupby(['Unnamed: 0', '0']).size().reset_index()[['Unnamed: 0', "0"]]



plt.bar(df_['Unnamed: 0'].tolist(),df_['0'].tolist(), width = 1000 )
plt.xlabel("buffer distance in feet")
plt.ylabel("count of nodes within")
plt.savefig("plt.png")