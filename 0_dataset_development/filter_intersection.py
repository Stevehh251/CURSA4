'''
    This script filters pages in one dir where the intersection in records is too large
'''

import sys
import json

from glob import glob

def intersect(first : set, second : set):
    return len(first.intersection(second)) / len(second)

class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def filter_intersection(filelist: list):
    """
        This function returns a list of files that should be included in the dataset
        
        @type filelist: string
        @param list: List of initial filenames
        
        @rtype: list
        @return: List of filtered filenames
    """

    # folder_path = sys.argv[1]
    # folder = glob(folder_path + "*.json")
   
    # Set of all records in directory
    all_records = set()
    
    # List of filenames that we will add to the dataset
    good_files = list()

    for filename in filelist:
        
        with open(filename, "r") as _file:
            _data = json.load(_file)
            _data = _data["info"]
            file_records = []
            for d in _data:
                if d is None:
                    continue
                if hasattr(d["title"], "strip"): # this is string
                    if len(d["title"]):
                        file_records.append(d["title"])
                elif hasattr(d["title"], "__iter__"):
                    if len(d["title"]):
                        file_records.append(d["title"][0])
            # file_records = [d["title"] if hasattr(d["title"], "strip") else d["title"][0] for d in _data]
            # print(file_records)
            file_records = tuple(file_records)
            file_records = set(file_records)
            
        if len(file_records) != 0 and intersect(all_records, file_records) <= 0.25:
            all_records = all_records.union(file_records)
            # print(len(all_records))
            good_files.append(filename)
      
    return good_files
    