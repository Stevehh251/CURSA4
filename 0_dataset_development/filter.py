import re
import sys
import os
import shutil
import json 

import numpy as np
from cleaners import clean_html
from css_extractor import extract
from sklearn.model_selection import StratifiedGroupKFold
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
            Out_path/train -> train_part
            Out_path/test -> test_part
        
    '''
    '''
        TODO: Add page cleaner
        TODO: Clear \n and \t from html
    '''
    
    input_folder_path = os.path.abspath(sys.argv[1])
    output_folder_path = os.path.abspath(sys.argv[2])
    css_folder_path = os.path.abspath(sys.argv[3])
    
    # folder_path = "html/"
    filenames = glob(input_folder_path + "*.json")
    
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
            # try:
            a = filter_intersection(filename_groups[group_name])
            good_filenames = good_filenames.union(a)
            after += len(a)
            # except Exception as e:
            #     print(e, group_name)
        
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
        max_number_of_page = 200
        
        filename_groups = defaultdict(list)
        filenames_after_filtration = set()
        before = len(good_filenames)
        
        for filename in good_filenames:
            group_name = re.search(r'.*(?=_)', filename)
            filename_groups[group_name[0]].append(filename)
            
        for group_name in filename_groups.keys():
            filename_groups[group_name] = filename_groups[group_name][:max_number_of_page]
            for filename in filename_groups[group_name]:
                filenames_after_filtration.add(filename)
        
        good_filenames = filenames_after_filtration
        after = len(good_filenames)
        print(f"Was filtered (Page number restriction): {before - after}")
        print(f"After filtration (Page number restriction) : {after}")
    
    # Train / Test split
    if (True):
        groups = []
        group_num = {}

        classes = []
        
        good_filenames = list(good_filenames)
        
        info = extract(good_filenames, css_folder_path)
        
        for filename in good_filenames:
            # group detect
            group_name = re.search(r'.*(?=_)', filename)[0]
            if not(group_name in group_num.keys()):
                group_num[group_name] = len(group_num.keys())

            groups.append(group_num[group_name])
            #class detect

            file_labels = info[filename]["exist_labels"]

            file_labels = sorted(file_labels)
            file_labels = tuple(file_labels)
            classes.append(hash(file_labels))

        spl = StratifiedGroupKFold(n_splits=4)
        

        for (train_idx_local, test_idx_local) in spl.split(good_filenames, classes, groups):

            train_idx = train_idx_local
            test_idx = test_idx_local

            train_groups = set([groups[idx] for idx in train_idx])
            test_groups = set([groups[idx] for idx in test_idx])
            
            print(train_groups)
            print(test_groups)
            break

        train = [good_filenames[idx] for idx in train_idx] 
        test = [good_filenames[idx] for idx in test_idx] 


        os.mkdir(output_folder_path)
        os.mkdir(output_folder_path + "/train")
        os.mkdir(output_folder_path + "/test")

        for filename in train:
            file = os.path.basename(filename)
            shutil.copyfile(filename, output_folder_path + "/train" + "/" + file)
            with open(output_folder_path + "/train" + "/" + file, "w", encoding="utf-8") as f: 
                info = json.load(f)
                
                html = json.loads(info['html'])
                html = clean_html(html)
                info['html'] = html
                
                json.dump(html, f, ensure_ascii=False, indent=4)
            
            
        for filename in test:
            file = os.path.basename(filename)
            shutil.copyfile(filename, output_folder_path + "/test" + "/" + file)
            
            with open(output_folder_path + "/test" + "/" + file, "w", encoding="utf-8") as f: 
                info = json.load(f)
                
                html = json.loads(info['html'])
                html = clean_html(html)
                info['html'] = html
                
                json.dump(html, f, ensure_ascii=False, indent=4)
        