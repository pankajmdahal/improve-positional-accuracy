# the original file was first randomized and sample of different sizes were taken
# and then again sorted

import pandas
import numpy

file_name = 'base.dat'

with open(file_name, 'r') as f:
    all_data = [line.split(',') for line in f.readlines()]

total_size = len(all_data)
sizes = [100, 200, 500, 1000, 5000, 10000, 20000, 30000, 50000, 70000, 80000, total_size]

# random.shuffle(all_data)

base_df = pandas.DataFrame(all_data)
base_df['comm'] = base_df[0].str[0:5]
base_df['ONode'] = base_df[0].str[5:10]
base_df['DNode'] = base_df[0].str[10:15]
base_df['quantity'] = base_df[0].str[15:25]
base_df['startRR'] = base_df[0].str[25:30]

# randomize
base_df = base_df.sample(frac=1)

# convert all the required data to integer since mapping for integers only works for integers
base_df.comm = base_df.comm.astype(int)
base_df.ONode = base_df.ONode.astype(int)
base_df.DNode = base_df.DNode.astype(int)
base_df.quantity = base_df.quantity.astype(float)
base_df.startRR = base_df.startRR.astype(int)

base_df['comm'] = base_df['comm'].map('{:5d}'.format)
base_df['ONode'] = base_df['ONode'].map('{:5d}'.format)
base_df['DNode'] = base_df['DNode'].map('{:5d}'.format)
base_df['quantity'] = base_df['quantity'].map('{:10.1f}'.format)
base_df['startRR'] = base_df['startRR'].map('{:5d}'.format)

for N in sizes:
    base_df1 = base_df.head(N)
    base_df1 = base_df1.sort_values(by=['comm', 'ONode', 'DNode', 'startRR'])
    base_df1 = base_df1[["comm", "ONode", "DNode", "quantity","startRR"]]
    base_df1 = base_df1[['comm', 'ONode', 'DNode', 'quantity', 'startRR']].apply(
        lambda x: '{}{}{}{}{}'.format(x[0], x[1], x[2], x[3], x[4]), axis=1)
    base_df1.to_csv("b" + str(N) + ".dat", index=False)
