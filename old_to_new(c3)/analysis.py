from sklearn import preprocessing
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import RFE
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve
from sklearn import metrics
import statsmodels.api as sm
import seaborn as sns
import pandas as pd
import numpy as np

threshold_for_many_y = 0.01  # miles
min_distance_to_ground = {}

# column names
dev_min_sod = "dev_min_sod"
oid = 'old_id'
nid = 'new_id'
sod = 'sod'
overlapped = 'overlapped'
no_conn = 'no_conn'
dist_to_ground = 'dist_to_ground'
oid_nid_dist = 'dist'
y = 'y'


# functions

# calculation of minimum distance ground for each set or {oid: {nid:min_distance_to_ground}}
# only one allowed per oid_nid

def calc_min_oid_nid_dist(_oid_, _nid_, curr_dist_g):
    if _oid_ in min_distance_to_ground:
        if curr_dist_g < list(min_distance_to_ground[_oid_].values())[0]:
            min_distance_to_ground[_oid_] = {}
            min_distance_to_ground[_oid_][_nid_] = curr_dist_g
    else:
        min_distance_to_ground[_oid_] = {_nid_: curr_dist_g}


# y=1 for nid with min ground_dist for each oid
def get_y(oid, nid):
    if nid in list(min_distance_to_ground[oid].keys()):
        return 1
    else:
        return 0


# get other y's (within threshold from the main y)
def get_many_y(old, new, y, min_sod):
    sod_at_1 = list(data_df[(data_df.old_id == old) & (data_df.y == 1)][dev_min_sod])
    if type(sod_at_1) == list:
        sod_at_1 = sod_at_1[0]
    if y == 1:
        return 1
    else:
        if abs(min_sod - sod_at_1) < threshold_for_many_y:
            # print ("{0}->{1}".format(min_sod, sod_at_1))
            return 1
        else:
            return 0


#
def calc_dev_from_min_sod(id, sod):
    if id in od_min_sod:
        if od_min_sod[id] > sod:
            od_min_sod[id] = sod
    else:
        od_min_sod[id] = sod


def get_most_likely_ground_dist(old_id, new_id):
    # if only one nearest ground truth present, return it
    if len(nearest_ground_truth_dict[new_id]) == 1:
        return list(nearest_ground_truth_dict[new_id].values())[0]
    # return the one that repeats the most around the buffer
    list_of_new_nodes_around_old_node = list(all_dict[old_id].keys())
    repetation = {}
    try:
        for new_node in list_of_new_nodes_around_old_node:
            nearest_gt_dict = nearest_ground_truth_dict[new_node]
            for gt in nearest_gt_dict.keys():
                repetation[gt] = 0
            for id in repetation.keys():
                if id in nearest_gt_dict.keys():  # calculate the cumulative distance for each new_node
                    repetation[id] = repetation[id] + nearest_gt_dict[id]
        near_ground_id = min(repetation, key=repetation.get)
        return nearest_ground_truth_dict[new_id][near_ground_id]
    except:
        try:
            ngtd = nearest_ground_truth_dict[new_id]
            nearest_node = min(ngtd, key=ngtd.get)
            # print("{0}->{1}".format(old_id, new_id))
            return ngtd[nearest_node]
        except:
            print("Please update nearest ground truth dict with greater buffer distance and count")
            print("{0}->{1}".format(old_id, new_id))
            return 99999


def get_dev_min_sod_val(id, sod):
    return abs(od_min_sod[int(id)] - sod)


def get_simplified_df(all_dict_old):
    list_ = []
    for _old_id_, b in all_dict_old.items():
        for _new_id_, y in b.items():
            try:
                dist_ = [k[1] for k in ids_nearids_dist_dict[_old_id_] if k[0] == _new_id_][0]
            except:
                dist_ = 9999
            # nearest_ground_truth_dict[x]
            list_.append([_old_id_, _new_id_, y[0], y[1], count_connections[_old_id_],
                          get_most_likely_ground_dist(_old_id_, _new_id_), dist_])
    data_df = pd.DataFrame(list_)
    data_df = data_df.rename(
        columns={0: oid, 1: nid, 2: sod, 3: overlapped, 4: no_conn, 5: dist_to_ground, 6: oid_nid_dist})
    return data_df


od_min_sod = {}
all_dict = np.load('all_ids_dist_dict.npy', allow_pickle=True, encoding='latin1').item()
count_connections = np.load('count_connections.npy', allow_pickle=True, encoding='latin1').item()
nearest_ground_truth_dict = np.load('nearest_ground_truth_dict.npy', allow_pickle=True, encoding='latin1').item()
ids_nearids_dist_dict = np.load('ids_nearids_dist_dict.npy', allow_pickle=True, encoding='latin1').item()

# data preparation
all_old_nodes = all_dict.keys()
all_new_nodes = [y.keys() for x, y in all_dict.items()]

data_df = get_simplified_df(all_dict)

dumm = data_df.apply(lambda x: calc_min_oid_nid_dist(x[oid], x[nid], x[dist_to_ground]), axis=1)
dumm = data_df.apply(lambda x: calc_dev_from_min_sod(x[oid], x[sod]), axis=1)

# calculation of y and dev min sod
data_df[y] = data_df.apply(lambda x: get_y(x[oid], x[nid]), axis=1)
data_df[dev_min_sod] = data_df.apply(lambda x: get_dev_min_sod_val(x[oid], x[sod]), axis=1)

b1 = data_df
data_df = b1

# get_many_y
data_df_true = data_df[data_df.y == 1]
data_df['y1'] = data_df.apply(lambda x: get_many_y(x[oid], x[nid], x[y], x[dev_min_sod]), axis=1)
data_df[y] = data_df['y1']

data_df.to_csv("backup.csv")

b2 = data_df
data_df = b2

exceptions = data_df[(data_df[dev_min_sod] > 999999) | (data_df.dist > 9999)]
exceptions.to_csv("exceptions.csv")

# remove the data where the route is not found
# if routes not found for y=1, remove all
# if routes not found for y=0, remove only that

# the oids for which at least one value of sod > 999999
oid_1 = list(set(
    data_df[(data_df[sod] >= 999999)][oid].to_list()))  # 999999 is when a route is not found
# the oids for which at least one value of sod < 999999
oid_2 = list(set(
    data_df[(data_df[sod] <= 999999)][oid].to_list()))
oids_with_all_routes_not_found = [x for x in oid_1 if x not in oid_2]
data_df = data_df[~data_df[oid].isin(oids_with_all_routes_not_found)]
data_df = data_df[data_df[dev_min_sod] < 9999]

data_df.to_csv("check.csv")

b3 = data_df

# analysis
# parameters
plt.rc("font", size=14)
sns.set(style="white")
sns.set(style="whitegrid", color_codes=True)
pd.set_option('display.width', 100)

# descriptive statistics
data_df = b3
independent_variables = [oid_nid_dist, dev_min_sod, overlapped, no_conn]
all_variables = independent_variables.copy()
all_variables.append(y)

data_df = data_df[all_variables]

data_df0 = data_df[data_df.y == 0]
data_df1 = data_df[data_df.y == 1]

data_df_ = data_df0.append(data_df1)

#
# using lmsod or min_sod
x_df = data_df_[independent_variables]
y_df = data_df_[[y]]

# model
logit_model = sm.Logit(y_df, x_df)
result = logit_model.fit()
print(result.summary2())

data_df_['predicted'] = result.predict(x_df)
#
data_df_.to_csv("dog.csv")

X_train, X_test, y_train, y_test = train_test_split(x_df, y_df, test_size=0.2, random_state=5)
logreg = LogisticRegression()
logreg.fit(X_train, y_train)
y_pred = logreg.predict(X_test)
#
#
print('Accuracy of logistic regression classifier on test set: {:.2f}'.format(logreg.score(X_test, y_test)))

from sklearn.metrics import confusion_matrix

confusion_matrix = confusion_matrix(y_test, y_pred)
print(confusion_matrix)
tp = confusion_matrix[0][0]
fp = confusion_matrix[0][1]
fn = confusion_matrix[1][0]
tn = confusion_matrix[1][1]

# #
recall = tp / (tp + fn)  # sensitivity, hit rate
precision = tp / (tp + fp)  # positive predicted value
specificity = tn / (tn + fp)  # TNR
accuracy = (tp + tn) / (tp + tn + fp + fn)

print("Sensitivity/Recall: {0}".format(recall))
print("Specificity/TNR: {0}".format(specificity))
print("Precision/PPV: {0}".format(precision))
print("Accuracy: {0}".format(accuracy))

# ROC curve

logit_roc_auc = roc_auc_score(y_test, logreg.predict(X_test))
fpr, tpr, thresholds = roc_curve(y_test, logreg.predict_proba(X_test)[:, 1])
plt.figure()
plt.plot(fpr, tpr, label='Logistic Regression (area = %0.2f)' % logit_roc_auc)
plt.plot([0, 1], [0, 1], 'r--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic')
plt.legend(loc="lower right")
plt.savefig('Log_ROC')
plt.show()
