#!/usr/bin/env python3

from src.agents.expansion_agent import ExpansionAgent
from src.llm.ollama_client import OllamaClient
from src.config import Config
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

config = Config()
llm = OllamaClient()

print('🔬 Debug: Testing clustering with identical products...')

# Get 3 identical expansions
expansion_agent = ExpansionAgent(llm, config)
produtos_expandidos = []
for i in range(3):
    result = expansion_agent.run('CHIP TIM PRÉ PLANO NAKED 4G')
    produtos_expandidos.append(result['result'])

# Build the exact same text the AggregationAgent uses
textos = []
for produto in produtos_expandidos:
    texto = f"{produto['categoria_principal']} {produto['material_predominante']} {produto['descricao_expandida']} {' '.join(produto['palavras_chave_fiscais'])}"
    textos.append(texto)

print(f'Texts for clustering:')
for i, texto in enumerate(textos):
    print(f'  {i+1}: {texto[:100]}...')

# Test if texts are truly identical
print(f'\nTexts identical: {textos[0] == textos[1] == textos[2]}')

# Test TF-IDF vectorization
vectorizer = TfidfVectorizer(max_features=1000, stop_words=['portuguese'])
try:
    tfidf_matrix = vectorizer.fit_transform(textos)
    print(f'\nTF-IDF matrix shape: {tfidf_matrix.shape}')
    print(f'TF-IDF matrix density: {tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1]):.4f}')
    
    # Check if vectors are identical
    vec1 = tfidf_matrix[0].toarray()
    vec2 = tfidf_matrix[1].toarray()
    vec3 = tfidf_matrix[2].toarray()
    
    vec1_equals_vec2 = np.allclose(vec1, vec2)
    vec2_equals_vec3 = np.allclose(vec2, vec3)
    
    print(f'TF-IDF vectors identical: vec1==vec2: {vec1_equals_vec2}, vec2==vec3: {vec2_equals_vec3}')
    
    # Test K-Means with identical vectors
    n_clusters = min(3, max(1, len(produtos_expandidos) // 5))
    print(f'K-Means n_clusters: {n_clusters}')
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(tfidf_matrix)
    
    print(f'Cluster labels: {cluster_labels}')
    print(f'Unique clusters: {len(set(cluster_labels))}')
    
except Exception as e:
    print(f'Error in TF-IDF: {e}')
    
    # Try with different stop words or no stop words
    print('Trying without stop words...')
    vectorizer2 = TfidfVectorizer(max_features=1000)
    try:
        tfidf_matrix2 = vectorizer2.fit_transform(textos)
        print(f'TF-IDF matrix shape (no stop words): {tfidf_matrix2.shape}')
        
        kmeans2 = KMeans(n_clusters=3, random_state=42, n_init=10)
        cluster_labels2 = kmeans2.fit_predict(tfidf_matrix2)
        print(f'Cluster labels (no stop words): {cluster_labels2}')
    except Exception as e2:
        print(f'Error without stop words: {e2}')
