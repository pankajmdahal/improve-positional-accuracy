from sklearn import preprocessing
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import RFE
from sklearn.metrics import roc_auc_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import roc_curve
from sklearn import metrics
import statsmodels.api as sm
import seaborn as sns
import pandas as pd
import numpy as np

buffer_dist_lim = 2.5

min_distance_to_ground = {}
threshold_for_many_y = 1  # miles (mnsod diff)

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
    # oid = 918
    # nid = 95817
    if nid in list(min_distance_to_ground[oid].keys()):
        return 1
    else:
        return 0


# get other y's (within threshold from the main y)
def get_the_right_y_pred(old, new, y, min_sod):
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


# distance to old_id, dist_to_ground
def get_most_likely_ground_node_dist(old_id, new_id):
    # old_id = 918
    # new_id = 95968
    # if only one nearest ground truth present, return it
    if new_id not in nearest_ground_truth_dict:  # no ground truths nearby
        dist_to_old_id = [x for x in ids_nearids_dist_dict[old_id] if x[0] == new_id][0][1]
        return 99, dist_to_old_id
    #
    if len(nearest_ground_truth_dict[new_id]) == 1:
        dist_to_old_id = [x for x in ids_nearids_dist_dict[old_id] if x[0] == new_id][0][1]
        dist_to_gr = list(nearest_ground_truth_dict[new_id].values())[0]
        return dist_to_gr, dist_to_old_id
    #
    # return the one that has the minimum sum of distance to old node and ground truth
    sod_to_old_gt = {}
    nearest_gt_dict = nearest_ground_truth_dict[new_id]
    for gt in nearest_gt_dict.keys():
        sod_to_old_gt[gt] = 0
    #
    for id in sod_to_old_gt.keys():
        new_ids_near_old_id = ids_nearids_dist_dict[old_id]
        ids_list = [x[0] for x in new_ids_near_old_id]
        if id in ids_list:
            dist_to_old_from_gt = [x[1] for x in new_ids_near_old_id if x[0] == id][0]
        else:
            dist_to_old_from_gt = 999  # (since the current node being evaluated is very far from old node)
        dist_to_old_from_curr = [x for x in ids_nearids_dist_dict[old_id] if x[0] == new_id][0][1]
        sod_to_old_gt[id] = dist_to_old_from_gt + dist_to_old_from_curr
    #
    near_ground_id = min(sod_to_old_gt, key=sod_to_old_gt.get)
    dist_to_gr = nearest_ground_truth_dict[new_id][near_ground_id]
    dist_to_old_id = [x for x in ids_nearids_dist_dict[old_id] if x[0] == new_id][0][1]
    return dist_to_gr, dist_to_old_id


def get_dev_min_sod_val(id, sod):
    return abs(od_min_sod[int(id)] - sod)


def get_simplified_df(all_dict_old):
    list_ = []
    for _old_id_, b in all_dict_old.items():
        for _new_id_, y in b.items():
            dist_all = get_most_likely_ground_node_dist(_old_id_, _new_id_)
            if dist_all[1] > buffer_dist_lim:
                continue
            list_.append([_old_id_, _new_id_, y[0], y[1], count_connections[_old_id_], dist_all[0], dist_all[1]])
    data_df = pd.DataFrame(list_)
    data_df = data_df.rename(
        columns={0: oid, 1: nid, 2: sod, 3: overlapped, 4: no_conn, 5: dist_to_ground, 6: oid_nid_dist})
    return data_df


od_min_sod = {}
all_dict = np.load('./intermediate/all_ids_dist_dict.npy', allow_pickle=True, encoding='latin1').item()
count_connections = np.load('./intermediate/old_node_connections_dict.npy', allow_pickle=True, encoding='latin1').item()
count_connections = {x: len(y) for x, y in count_connections.items()}
nearest_ground_truth_dict = np.load('./intermediate/nearest_ground_truth_dict.npy', allow_pickle=True,
                                    encoding='latin1').item()
ids_nearids_dist_dict = np.load('./intermediate/ids_nearids_dist_dict.npy', allow_pickle=True, encoding='latin1').item()

# data preparation

all_dict = {x: y for x, y in all_dict.items() if y != {99999: [99999, 99999]}}
all_old_nodes = all_dict.keys()
all_new_nodes = [y.keys() for x, y in all_dict.items()]

data_df = get_simplified_df(all_dict)

dumm = data_df.apply(lambda x: calc_min_oid_nid_dist(x[oid], x[nid], x[dist_to_ground]), axis=1)
dumm = data_df.apply(lambda x: calc_dev_from_min_sod(x[oid], x[sod]), axis=1)

# calculation of y and dev min sod
data_df[y] = data_df.apply(lambda x: get_y(x[oid], x[nid]), axis=1)
data_df[dev_min_sod] = data_df.apply(lambda x: get_dev_min_sod_val(x[oid], x[sod]), axis=1)

b1 = data_df.copy()
data_df = b1.copy()

data_df['y_pred'] = np.where(((data_df.dev_min_sod <= threshold_for_many_y) & (data_df.y == 1)), 1,
                             0)  # all below threshold is predicted 1

summary = pd.pivot_table(data_df, values=["y_pred"], index=["old_id"], aggfunc=np.sum).reset_index()
list_of_dev_min_sod_ids = summary[summary.y_pred == 0]['old_id'].to_list()

data_df['y_pred'] = np.where(((data_df.old_id.isin(list_of_dev_min_sod_ids)) & (data_df.dev_min_sod == 0)), 1,
                             data_df.y_pred)  # all below threshold is predicted 1

data_df.to_csv("ddd.csv")

# data_df = data_df[((data_df.dev_min_sod == 0) | (data_df.y == 1)) ]

data_df = data_df[['y', 'y_pred']]
# data_df.to_csv("apple.csv")
data_df = data_df.replace({0: 1, 1: 0})
cm = confusion_matrix(data_df['y_pred'], data_df['y'])
print(cm)
tp = cm[0][0]
fp = cm[0][1]
fn = cm[1][0]
tn = cm[1][1]
# #
recall = tp / (tp + fn)  # sensitivity, hit rate
precision = tp / (tp + fp)  # positive predicted value
specificity = tn / (tn + fp)  # TNR
accuracy = (tp + tn) / (tp + tn + fp + fn)
f1 = 2 * recall * precision / (recall + precision)
print("Sensitivity/Recall: {0}".format(recall))
print("Precision/PPV: {0}".format(precision))
print("Specificity/TNR: {0}".format(specificity))
print("Accuracy: {0}".format(accuracy))
print("F1: {0}".format(f1))
