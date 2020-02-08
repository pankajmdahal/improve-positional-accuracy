import re
import pandas as pd
import Levenshtein as lev
from fuzzywuzzy import process

df1 = pd.DataFrame({'Code':[], 'sctg':[]})

#regex = re.compile("(\D+) (\w{2,4}) (\d{3}\s)")
regex = re.compile("([0-9-]*)([\w, ()-]*)")


with open("sctg.csv") as f:
   for line in f:
      if len(line.split()) != 0:
         result = regex.search(line)
         new = pd.DataFrame({'Code':[result.group(1)], 'sctg':[result.group(2)]})
         df1 = df1.append(new)

#df1.to_csv("AARCode.csv", ignore_index=True)


str2Match = "apple inc"
strOptions = ["Apple Inc.","apple park","apple incorporated","iphone"]
# You can also select the string with the highest matching percentage
highest = process.extractOne(str2Match,strOptions)
print(highest)



df2 = pd.read_csv("../../shortlines_project/conversion.csv")


for i in range(10):
   highest_j = 0
   _j_=0 #jth element would have the highest
   for j in range(len(df2)):
      highest_new = process.extractOne(df1.iloc[i]['sctg'].lower(), df2.iloc[j]['0'].lower())
      if highest_new[1] > highest_j:
         highest_j = highest_new
         _j_ = j
   df1.iloc[i]['new'] = df2.iloc[_j_]['1']
