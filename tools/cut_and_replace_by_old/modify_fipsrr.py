import pandas as pd
import numpy as np
from params import *



fips_abbr = pd.read_csv(abbr_to_fips)
fipsrr_df = pd.read_csv(fips_rr_input)

fips_abbr_dict = fips_abbr.transpose().to_dict()
fips_abbr_dict = { y['abbr']:int(y['fips']) for x,y in fips_abbr_dict.iteritems()}

clip_fips_list = [fips_abbr_dict[x[1:-1]] for x in clip_state_list]


fipsrr_df['node_state'] = fipsrr_df['NODE']/1000
fipsrr_df['node_state'] = fipsrr_df['node_state'].apply(np.floor)
fipsrr_df = fipsrr_df[~fipsrr_df.node_state.isin(clip_fips_list)].reset_index()[['FIPS','RR', 'NODE', 'DIST']]


fipsrr_df.to_csv(fips_rr_output)







