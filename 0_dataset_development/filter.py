import re
import sys
import os
import shutil
import json 

import numpy as np

from tqdm import tqdm
from glob import glob
from collections import defaultdict
from filter_intersection import filter_intersection
from checkers import bs_checker
from difflib import SequenceMatcher
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

if __name__ == "__main__":
    
    '''
        Folder_path - path to folder with jsons with data
        
        Out_path -> path to three folders:
            Out_path -> full dataset
            Out_path_train -> train_part
            Out_path_test -> test_part
        
    '''
    
    folder_path = sys.argv[1]
    out_path = sys.argv[2]
    
    
    
    
    # folder_path = "html/"
    filenames = glob(folder_path + "*.json")
    
    # Set for ended filenames in dataset 
    good_filenames = set()
    
    # For app_example.com_86.json group name is app_example.com
    if (True):
        filename_groups = defaultdict(list)
        
        for filename in filenames:
            group_name = re.search(r'.*(?=_)', filename)
            filename_groups[group_name[0]].append(filename)
        
        # Intersection filtration stage
        before = 0
        after = 0
        for group_name in filename_groups.keys():
            
            before += len(filename_groups[group_name])
            try:
                a = filter_intersection(filename_groups[group_name])
                good_filenames = good_filenames.union(a)
                after += len(a)
            except Exception:
                print(group_name)
        
        print(f"Was filtered (intersection): {before - after}")
        print(f"After filtration (intersection) : {after}")

    # BS soup checker stage
    if (False) :
        before = 0
        after = 0
        to_filter = good_filenames.copy()
        for filename in tqdm(to_filter):
            before += 1
            after += 1
            if not bs_checker(filename) :
                good_filenames.remove(filename)
                after -= 1
            
        
        print(f"Was filtered (BS checker): {before - after}")
        print(f"After filtration (BS checker) : {after}")
    
    # Page number restriction
    
    if (True):
        max_number_of_page = 30
        
        filename_groups = defaultdict(list)
        new_filenames = set()
        before = len(good_filenames)
        
        for filename in good_filenames:
            group_name = re.search(r'.*(?=_)', filename)
            filename_groups[group_name[0]].append(filename)
            
        for group_name in filename_groups.keys():
            filename_groups[group_name] = filename_groups[group_name][:max_number_of_page]
            for filename in filename_groups[group_name]:
                new_filenames.add(filename)
        
        good_filenames = new_filenames
        after = len(good_filenames)
        print(f"Was filtered (Page number restriction): {before - after}")
        print(f"After filtration (Page number restriction) : {after}")
    
    
    # Train / Test split
    if (False):
        similar_data = []
        filename_groups = defaultdict(list)
        
        for filename in good_filenames:
            group_name = re.search(r'.*(?=_)', filename)
            filename_groups[group_name[0]].append(filename)
        
        all_pages = 0
        
        for first_domain in filename_groups.keys():
            for second_domain in filename_groups.keys():
            
                first_domain_len = len(filename_groups[first_domain])
                all_pages += first_domain_len
                second_domain_len = len(filename_groups[second_domain])
            
                similar_data.append((similar(first_domain, second_domain),
                                    first_domain_len + second_domain_len,
                                    first_domain, second_domain))
        
        max_similar = 0.8
        similar_data = list(filter(lambda x : 1.0 > x[0] > max_similar, similar_data))
        similar_data = sorted(similar_data)[::2]
        
        # print(*similar_data, sep='\n')
        # print(len(similar_data))

    if (False):
        similar_data = []
        filename_groups = defaultdict(list)
        
        for filename in good_filenames:
            group_name = re.search(r'.*(?=_)', filename)
            filename_groups[group_name[0]].append(filename)
        
        filelist = list(good_filenames)

        idx = 0
        groups = []
        group_num = {}
        for filename in filelist:
            group_name = re.search(r'.*(?=_)', filename)
            if not(group_name in group_num):
                group_num[group_name] = idx
                idx += 1
            groups.append(group_num[group_name])

        classes = []




        all_pages = 0

        train_part = 0.7
        total_len = len(good_filenames)

        train = []
        test = []
        for domain in filename_groups.keys():
            if (len(train) + len(filename_groups[domain]) < train_part * total_len):
                train += filename_groups[domain]
            else:
                test += filename_groups[domain]
        
        
    # prefix = "test_marking"
    
    os.mkdir(out_path)
    
    for filename in good_filenames:
        file = os.path.basename(filename)
        shutil.copyfile(filename, out_path + "/" + file)
        
    os.mkdir(out_path + "_train")
    
    for filename in train:
        file = os.path.basename(filename)
        shutil.copyfile(filename, out_path + "_train" + "/" + file)
        
    os.mkdir(out_path + "_test")
    
    for filename in test:
        file = os.path.basename(filename)
        shutil.copyfile(filename, out_path + "_test" + "/" + file)
        