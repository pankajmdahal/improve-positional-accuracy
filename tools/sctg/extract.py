import re
import pandas as pd
import Levenshtein as lev
from fuzzywuzzy import process

df1 = pd.DataFrame({'Code':[], 'sctg':[]})

#regex = re.compile("(\D+) (\w{2,4}) (\d{3}\s)")
regex = re.compile("([0-9-]*)([\w, ()-]*)")

word_re_dict = {}


with open("sctg.csv") as f:
   for line in f:
      if len(line.split()) != 0:
         result = regex.search(line)
         excluded = ["click to collapse contents"]
         final_text = result.group(2)
         for excluded_ in excluded:
            final_text = re.sub(excluded_, ' ',final_text)
         new = pd.DataFrame({'Code':[result.group(1)], 'sctg':[final_text]})
         df1 = df1.append(new)

df1.to_csv("stcg_simplified.csv")

def get_percent_of_common_words(A, B):
   # use dict to store word and its re
   A_replace_dict = {'[~!@#$%^&*()_+,.0123456789-]':""}
   B_replace_dict = {'[~!@#$%^&*()_+,.0123456789-]':""}
   if A in word_re_dict:
      final_string_A = word_re_dict[A]
   else:
      final_string_A = A
      for key,value in A_replace_dict.iteritems():
         final_string_A = re.sub(key, value, final_string_A)
      word_re_dict[A] = final_string_A
   if B in word_re_dict:
      final_string_B = word_re_dict[B]
   else:
      final_string_B = B
      for key,value in B_replace_dict.iteritems():
         final_string_B = re.sub(key, value, final_string_B)
      word_re_dict[B] = final_string_B
   count = 0
   # insert words of string A to hash
   A_ = final_string_A.split()
   B_ = final_string_B.split()
   #if the first word matches, give higher priority
   if A_[0] == B_[0]:
      count = 2
   # return required list of words
   list_of_common_words = [x for x in A_ if x in B_]
   percent_match = float(count + len(list_of_common_words))/(len(A_) + len(B_))
   return percent_match


conv_df = pd.read_csv("conversion.csv")
df1 = df1.reset_index()[['Code', 'sctg']]

for i in range(len(conv_df)):
   #print i
   highest_j = 0
   _j_=0 #jth element would have the highest
   s1 = conv_df.iloc[i]['0']
   for j in range(len(df1)):
      s2 = df1.iloc[j]['sctg']
      highest_new = get_percent_of_common_words(s1,s2)
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
