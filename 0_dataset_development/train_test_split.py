from collections import defaultdict
from glob import glob
import sys
import re
import json
import os
import shutil

from sklearn.model_selection import StratifiedGroupKFold


folder_path = sys.argv[1]
out_path = folder_path

good_filenames = glob(folder_path + "*.json")
filelist = list(good_filenames)

idx = 0
groups = []
group_num = {}

classes = []

for filename in filelist:
    # group detect
    group_name = re.search(r'.*(?=_)', filename)[0]
    if not(group_name in group_num.keys()):
        group_num[group_name] = idx
        idx += 1

    groups.append(group_num[group_name])
    #class detect
    with open(filename) as file:
        info = json.load(file)
        file_labels = info["exist_labels"]

    file_labels = sorted(file_labels)
    file_labels = tuple(file_labels)
    classes.append(hash(file_labels))

spl = StratifiedGroupKFold(n_splits=4)

# with spl.split(filelist, classes, groups) as split:
    # train_idx, test_idx = split[0]
# train_idx, test_idx = spl.split(filelist, classes, groups)

for (train_idx_local, test_idx_local) in spl.split(filelist, classes, groups):

    train_idx = train_idx_local
    test_idx = test_idx_local

    train_groups = set([groups[idx] for idx in train_idx])
    test_groups = set([groups[idx] for idx in test_idx])
    
    print(train_groups)
    print(test_groups)
    break

train = [filelist[idx] for idx in train_idx] 
test = [filelist[idx] for idx in test_idx] 


    
os.mkdir(out_path + "_train")

for filename in train:
    file = os.path.basename(filename)
    shutil.copyfile(filename, out_path + "_train" + "/" + file)
    
os.mkdir(out_path + "_test")

for filename in test:
    file = os.path.basename(filename)
    shutil.copyfile(filename, out_path + "_test" + "/" + file)