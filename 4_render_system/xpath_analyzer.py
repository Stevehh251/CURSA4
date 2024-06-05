from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import numpy as np

from metrics import *

class xpath_analyzer:

    def __init__(self):
        self.vectorizer = CountVectorizer(
            tokenizer=lambda x: re.findall(r'(\/\w+|\[\d+\])', x), lowercase=False)

    def analyze(self, html, predicts, pred_block_prefix):
        all_xpath = generate_all_xpaths(html)
        
        X = []
        y = []
        for xpath in all_xpath:
            X.append(xpath)
            
            in_predicted_blocks = [path_contains(block_xpath.split('/'), xpath.split('/')) for
                                       block_xpath in pred_block_prefix]
            if xpath_label != 0 and any(in_predicted_blocks):
                y.append(label)
            elif xpath_label == 0 and not any(in_predicted_blocks):
                y.append(0)
    
    
    
    def clusterize(self, xpaths):
        vector_xpaths = self.vectorizer.fit_transform(xpaths)

        inertia = []
        silhouette_scores = []
        k_values = range(2, 10)  # Пробуем от 2 до 9 кластеров

        for k in k_values:
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(vector_xpaths)
            inertia.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(vector_xpaths, kmeans.labels_))

        optimal_k = k_values[silhouette_scores.index(max(silhouette_scores))]
        
        print(f"Оптимальное количество кластеров: {optimal_k}")
        
        kmeans = KMeans(n_clusters=optimal_k, random_state=42)
        kmeans.fit(vector_xpaths)

        labels = kmeans.labels_
        # print(labels)
        # return labels
    
    
        centroids = kmeans.cluster_centers_

        # Вычисление расстояний до центроидов
        distances = np.linalg.norm(vector_xpaths - centroids[labels], axis=1)

        # Определение порогового значения для аномалий (например, верхние 5% расстояний)
        threshold = np.percentile(distances, 95)

        # Выделение аномалий
        anomalies = np.where(distances > threshold)[0]
        print("a", anomalies)

        # Вывод результатов кластеризации и аномалий
        clusters = {i: [] for i in range(optimal_k)}
        for i, (xpath, label) in enumerate(zip(xpaths, labels)):
            clusters[label].append(xpath)

        print("Кластеры:")
        for cluster, clust_xpaths in clusters.items():
            print(f"Cluster {cluster}:")
            for xpath in clust_xpaths:
                print(f"    {xpath}")

        print("Аномалии:")
        for idx in anomalies:
            print(f"    {xpaths[idx]}")

    



to_analyze = ['/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/div[1]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[1]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[2]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[3]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/div[2]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[4]',
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[5]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[6]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/div[3]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[7]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[8]', 
              '/html/body/div/div/div/div[4]/div/div[2]/main/div[2]/div/div[2]/div/article[9]',
              '/html/body/div/div/div/div[4]/dav/div[2]/main/dav[2]/div/div[2]/div/article[9]',
              '/adasdadsad',
              '/dgergreger']
analyze = xpath_analyzer()
analyze.clusterize(to_analyze)
# vectorizer = CountVectorizer(tokenizer=lambda x: re.findall(r'//(\w+)|@(\w+)', x), lowercase=False)
# X_correct = vectorizer.fit_transform(correct_xpaths)
# X_incorrect = vectorizer.transform(incorrect_xpaths)
