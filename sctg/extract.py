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


def UncommonWords(A, B):
   # count will contain all the word counts
   count = 0
   # insert words of string A to hash
   A = A.split()
   B = B.split()
   if A[0] == B[0]:
      count = 2
   # return required list of words
   list_of_common_words = [x for x in A if x in B]
   return count + len(list_of_common_words)


conv_df = pd.read_csv("conversion.csv")
df1 = df1.reset_index()[['Code', 'sctg']]

for i in range(len(conv_df)):
   #print i
   highest_j = 0
   _j_=0 #jth element would have the highest
   s1 = re.sub('[~!@#$%^&*()_+,.0123456789-]', '', conv_df.iloc[i]['0'].lower())
   for j in range(len(df1)):
      s2 = re.sub('[~!@#$%^&*()_+,.0123456789-]', '', df1.iloc[j]['sctg'].lower()).strip()
      highest_new = UncommonWords(s1,s2)
      if highest_new > highest_j:
         #print "ENTERED"
         highest_j = highest_new
         _j_ = j
         _s2_ = s2
   if _j_ != 0:
      conv_df.at[i, 'new'] = df1.iloc[_j_]['Code']
      conv_df.at[i, 'desc'] = df1.iloc[_j_]['sctg']
      conv_df.at[i, 'count'] = highest_j
      #conv_df.at[i, 's2'] = _s2_
      #conv_df.at[i, 's1'] = s1

conv_df.to_csv("apple.csv")

re.sub('[~!@#$%^&*()_+ ]', '', "vnlad fyfg345$%$&*%^*%hfgh")
