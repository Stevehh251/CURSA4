import re
import sys
import os
import shutil
import json

from sklearn.model_selection import StratifiedGroupKFold
from tqdm import tqdm
from collections import defaultdict
from difflib import SequenceMatcher
from glob import glob

from cleaners import clean_html
from css_extractor import extract
from filter_intersection import filter_intersection
from checkers import bs_checker


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

    input_folder_path = os.path.abspath(sys.argv[1]) + '/'
    output_folder_path = os.path.abspath(sys.argv[2])
    css_folder_path = os.path.abspath(sys.argv[3])

    filenames = glob(input_folder_path + "*.json")

    good_filenames = set()  # Filenames which we should include into dataset

    if (True):
        """
            This part of code checks that each html page contains enough new records.
            If page contains not enough new records it should be filtered.
        """
        
        filename_groups = defaultdict(list)  # For 'app_example.com_86.json' group name is 'app_example.com'

        for filename in filenames:
            group_name = re.search(r'.*(?=_)', filename)
            filename_groups[group_name[0]].append(filename)

        before = 0
        after = 0
        for group_name in filename_groups.keys():
            before += len(filename_groups[group_name])
            remaining_filenames = filter_intersection(filename_groups[group_name])
            good_filenames = good_filenames.union(remaining_filenames)
            after += len(remaining_filenames)
        
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(f"Was filtered (intersection): {before - after}")
        print(f"After filtration (intersection) : {after}")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    if (False):
        """
            While working with data it maybe important to use 'correct' htmls.
            So this part of code check that beautifulsoup parser doesnt throw any warning.
        """
        
        before = 0
        after = 0
        to_filter = good_filenames.copy()
        for filename in tqdm(to_filter):
            before += 1
            after += 1
            if not bs_checker(filename):
                good_filenames.remove(filename)
                after -= 1

        print(f"Was filtered (BS checker): {before - after}")
        print(f"After filtration (BS checker) : {after}")

    if (True):
        """
            This part of code resricts amount of pages for each 'page group'(its domain).
        """

        # max_number_of_page = 200
        max_number_of_page = 3

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
        
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(f"Was filtered (Page number restriction): {before - after}")
        print(f"After filtration (Page number restriction) : {after}")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    if (True):
        """
            This part of code makes train/test split of dataset.
            In splitting takes into account label distribution for each page group.
        """
        groups = []  # groups[idx] = group number of good_filenames[idx] file
        group_num = {}  # for each group name contains its number

        classes = []  # for each good_filename contains its 'class_type' = hash('tuple with all labels of page')

        good_filenames = list(good_filenames)

        info = extract(good_filenames, css_folder_path)
        
        good_filenames = list(info.keys())
        
        for filename in good_filenames:
            # group detect
            group_name = re.search(r'.*(?=_)', filename)[0]
            if not (group_name in group_num.keys()):
                group_num[group_name] = len(group_num.keys())

            groups.append(group_num[group_name])
            # class detect

            file_labels = info[filename]["exist_labels"]

            file_labels = sorted(file_labels)
            file_labels = tuple(file_labels)
            classes.append(hash(file_labels))

        splitter = StratifiedGroupKFold(n_splits=4)

        for (train_idx_local, test_idx_local) in splitter.split(good_filenames, classes, groups):

            train_idx = train_idx_local
            test_idx = test_idx_local

            train_groups = set([groups[idx] for idx in train_idx])
            test_groups = set([groups[idx] for idx in test_idx])

            break

        train = [good_filenames[idx] for idx in train_idx]
        test = [good_filenames[idx] for idx in test_idx]

        os.mkdir(output_folder_path)
        os.mkdir(output_folder_path + "/train")
        os.mkdir(output_folder_path + "/test")

        for filename in train:
            name = os.path.basename(filename)
            shutil.copyfile(filename, output_folder_path + "/train" + "/" + name)
            with open(output_folder_path + "/train" + "/" + name, "r+", encoding="utf-8") as file:
                info = json.load(file)
   
                html = info['html']
                html = clean_html(html)
                info['html'] = html

                json.dump(html, file, ensure_ascii=False, indent=4)

        for filename in test:
            name = os.path.basename(filename)
            shutil.copyfile(filename, output_folder_path + "/test" + "/" + name)

            with open(output_folder_path + "/test" + "/" + name, "r+", encoding="utf-8") as file:
                info = json.load(file)

                html = info['html']
                html = clean_html(html)
                info['html'] = html

                json.dump(html, file, ensure_ascii=False, indent=4)
