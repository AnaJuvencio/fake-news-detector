"""
Módulo de avaliação de modelos para detecção de fake news.
Este módulo contém funções para avaliar modelos treinados usando
métricas clássicas e de fairness.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import joblib
import matplotlib.pyplot as plt
import seaborn as sns


class FakeNewsEvaluator:
    """Classe para avaliação de modelos de detecção de fake news."""
    
    def __init__(self, model_path, vectorizer_path):
        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)
    
    def evaluate_basic_metrics(self, X_test, y_test):
        """Calcula métricas básicas de classificação."""
        y_pred = self.model.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1': f1_score(y_test, y_pred, average='weighted')
        }
        
        return metrics, y_pred
    
    def plot_confusion_matrix(self, y_test, y_pred, title="Confusion Matrix"):
        """Plota matriz de confusão."""
        cm = confusion_matrix(y_test, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title(title)
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.show()
        
        return cm
    
    def evaluate_fairness_metrics(self, X_test, y_test, sensitive_attribute):
        """
        Calcula métricas de fairness como Demographic Parity (DI) e 
        Statistical Parity Difference (SPD).
        """
        y_pred = self.model.predict(X_test)
        
        # Calcula DI (Demographic Parity Index)
        groups = np.unique(sensitive_attribute)
        group_predictions = {}
        
        for group in groups:
            group_mask = (sensitive_attribute == group)
            group_pred = y_pred[group_mask]
            positive_rate = np.mean(group_pred == 1) if len(group_pred) > 0 else 0
            group_predictions[group] = positive_rate
        
        # DI = min_rate / max_rate
        rates = list(group_predictions.values())
        di = min(rates) / max(rates) if max(rates) > 0 else 1
        
        # SPD = |rate_group1 - rate_group2|
        if len(rates) == 2:
            spd = abs(rates[0] - rates[1])
        else:
            spd = max(rates) - min(rates)
        
        fairness_metrics = {
            'demographic_parity_index': di,
            'statistical_parity_difference': spd,
            'group_positive_rates': group_predictions
        }
        
        return fairness_metrics
    
    def generate_classification_report(self, y_test, y_pred):
        """Gera relatório detalhado de classificação."""
        return classification_report(y_test, y_pred)
    
    def predict_text(self, text):
        """Prediz a classe de um texto individual."""
        text_vectorized = self.vectorizer.transform([text])
        prediction = self.model.predict(text_vectorized)[0]
        probability = self.model.predict_proba(text_vectorized)[0]
        
        return {
            'prediction': 'fake' if prediction == 1 else 'real',
            'confidence': max(probability),
            'probabilities': {
                'real': probability[0],
                'fake': probability[1]
            }
        }


def compare_models(model_results):
    """Compara resultados de múltiplos modelos."""
    df_results = pd.DataFrame(model_results).T
    
    # Plot comparativo
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    
    for i, metric in enumerate(metrics):
        ax = axes[i//2, i%2]
        df_results[metric].plot(kind='bar', ax=ax, title=f'{metric.title()} Comparison')
        ax.set_ylabel(metric.title())
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    
    return df_results


if __name__ == "__main__":
    # Exemplo de uso
    print("Módulo de avaliação carregado. Use as classes para avaliar seus modelos.")