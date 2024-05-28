from collections import defaultdict
import matplotlib.pyplot as plt
import json
import sys
import os
from glob import glob
import matplotlib

matplotlib.use('pdf')

if __name__ == "__main__":
    folder_path = sys.argv[1]
    folder_path = os.path.abspath(folder_path)

    train_path = os.path.join(folder_path, "_train/")
    test_path = os.path.join(folder_path, "_test/")
    

    train_stats = defaultdict(int)
    for filename in glob(train_path + "*.json"):
        with open(filename) as file:
            labels = json.load(file)["exist_labels"]

        for label in labels:
            train_stats[label] += 1

    test_stats = defaultdict(int)
    for filename in glob(test_path + "*.json"):
        with open(filename) as file:
            labels = json.load(file)["exist_labels"]

        for label in labels:
            test_stats[label] += 1
    
    # for x, y in train_stats.items():
    #     print(x, y)

    plt.scatter(list(range(len(train_stats))), [train_stats[key] for key in train_stats.keys()], )
    plt.xticks(list(range(len(train_stats))),train_stats.keys() )
    print("Train Done")

    plt.scatter(list(range(len(test_stats))), [test_stats[key] for key in test_stats.keys()])
    plt.xticks(list(range(len(test_stats))), test_stats.keys() )
    plt.show()
    plt.legend(["train", "test"])
    plt.savefig("test.png")
    print("Test Done")