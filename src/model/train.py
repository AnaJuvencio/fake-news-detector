"""
Módulo de treinamento de modelos para detecção de fake news.
Este módulo contém funções para treinar diferentes algoritmos de ML
utilizando os datasets preprocessados.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os


class FakeNewsTrainer:
    """Classe para treinamento de modelos de detecção de fake news."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.models = {}
        
    def load_data(self, data_path):
        """Carrega dados preprocessados."""
        return pd.read_csv(data_path)
    
    def prepare_features(self, texts):
        """Prepara features usando TF-IDF."""
        return self.vectorizer.fit_transform(texts)
    
    def train_models(self, X_train, y_train):
        """Treina múltiplos modelos."""
        models = {
            'logistic_regression': LogisticRegression(random_state=42),
            'random_forest': RandomForestClassifier(random_state=42, n_estimators=100)
        }
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            self.models[name] = model
            print(f"Modelo {name} treinado com sucesso.")
    
    def evaluate_models(self, X_test, y_test):
        """Avalia todos os modelos treinados."""
        results = {}
        for name, model in self.models.items():
            y_pred = model.predict(X_test)
            results[name] = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted'),
                'recall': recall_score(y_test, y_pred, average='weighted'),
                'f1': f1_score(y_test, y_pred, average='weighted')
            }
        return results
    
    def save_models(self, output_dir):
        """Salva modelos treinados."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Salva vectorizer
        joblib.dump(self.vectorizer, os.path.join(output_dir, 'vectorizer.joblib'))
        
        # Salva modelos
        for name, model in self.models.items():
            joblib.dump(model, os.path.join(output_dir, f'{name}.joblib'))
            print(f"Modelo {name} salvo em {output_dir}")


if __name__ == "__main__":
    trainer = FakeNewsTrainer()
    # Exemplo de uso - descomentar e ajustar paths conforme necessário
    # data = trainer.load_data('../data/processed/combined_dataset.csv')
    # X = trainer.prepare_features(data['text'])
    # y = data['label']
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # trainer.train_models(X_train, y_train)
    # results = trainer.evaluate_models(X_test, y_test)
    # print(results)
    # trainer.save_models('../models')