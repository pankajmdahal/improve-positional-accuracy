import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


df = pd.read_csv("dist_v_no_of_links.csv")

sns.lineplot(x="Distance: ", y="Count of links completely within: ", markers=True, data=df)

plt.show()