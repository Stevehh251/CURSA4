from collections import defaultdict
import matplotlib.pyplot as plt
import json
import sys
import os
from glob import glob

if __name__ == "__main__":
    folder_path = sys.argv[1]
    folder_path = os.path.abspath(folder_path)

    s = 0
    print(len(glob(folder_path + "/*.json")))
    # pass
    # for filename in glob(folder_path + "/*.json"):
    #     with open(filename) as file:
    #         info = json.load(file)
    #     print(filename)
    #     s += len(info["xpaths"])

    # print(s)