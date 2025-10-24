"""
Carregador de modelos para a API de detecção de fake news.
Este módulo gerencia o carregamento e cache de modelos do S3 (LocalStack).
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import os
import sys
import tempfile
import joblib
from datetime import datetime

# Adiciona path para imports locais
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from storage.s3_client import S3Client
except ImportError as e:
    logging.warning(f"S3Client não disponível: {e}")
    S3Client = None

logger = logging.getLogger(__name__)


class ModelLoader:
    """Gerenciador de carregamento de modelos do S3."""
    
    def __init__(self, s3_config: Dict[str, str]):
        """
        Inicializa o carregador de modelos.
        
        Args:
            s3_config: Configuração do S3 contendo:
                - endpoint_url: URL do LocalStack
                - bucket_name: Nome do bucket
                - model_key: Chave do modelo no S3
                - vectorizer_key: Chave do vectorizer no S3
        """
        self.s3_config = s3_config
        self.s3_client = None
        self.model = None
        self.vectorizer = None
        self.model_info = {}
        self.last_loaded = None
        
        # Inicializa cliente S3 se disponível
        if S3Client:
            try:
                self.s3_client = S3Client(endpoint_url=s3_config['endpoint_url'])
                logger.info("S3Client inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar S3Client: {e}")
    
    async def load_model(self) -> bool:
        """
        Carrega modelo e vectorizer do S3.
        
        Returns:
            True se carregamento bem-sucedido, False caso contrário
        """
        try:
            if not self.s3_client:
                logger.error("S3Client não está disponível")
                return await self._load_local_fallback()
            
            # Tenta carregar do S3
            bucket_name = self.s3_config['bucket_name']
            model_key = self.s3_config['model_key']
            vectorizer_key = self.s3_config['vectorizer_key']
            
            logger.info(f"Carregando modelo de s3://{bucket_name}/{model_key}")
            
            # Carrega modelo
            self.model = self.s3_client.download_model(bucket_name, model_key)
            if not self.model:
                logger.error("Falha ao carregar modelo do S3")
                return await self._load_local_fallback()
            
            # Carrega vectorizer
            self.vectorizer = self.s3_client.download_model(bucket_name, vectorizer_key)
            if not self.vectorizer:
                logger.error("Falha ao carregar vectorizer do S3")
                return await self._load_local_fallback()
            
            # Atualiza informações do modelo
            self.model_info = {
                'source': 's3',
                'bucket': bucket_name,
                'model_key': model_key,
                'vectorizer_key': vectorizer_key,
                'loaded_at': datetime.now().isoformat(),
                'model_type': type(self.model).__name__
            }
            
            self.last_loaded = datetime.now()
            logger.info("Modelo carregado com sucesso do S3")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo do S3: {e}")
            return await self._load_local_fallback()
    
    async def _load_local_fallback(self) -> bool:
        """
        Fallback para carregar modelos locais se S3 não estiver disponível.
        """
        try:
            # Procura por modelos locais na pasta models/
            models_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
            
            if not os.path.exists(models_dir):
                logger.warning("Diretório de modelos locais não existe")
                return await self._load_dummy_model()
            
            # Procura arquivos de modelo
            model_files = [f for f in os.listdir(models_dir) if f.endswith('.joblib')]
            
            if not model_files:
                logger.warning("Nenhum modelo local encontrado")
                return await self._load_dummy_model()
            
            # Carrega primeiro modelo encontrado
            model_path = os.path.join(models_dir, model_files[0])
            vectorizer_path = os.path.join(models_dir, 'vectorizer.joblib')
            
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info(f"Modelo local carregado: {model_path}")
            
            if os.path.exists(vectorizer_path):
                self.vectorizer = joblib.load(vectorizer_path)
                logger.info(f"Vectorizer local carregado: {vectorizer_path}")
            
            if self.model and self.vectorizer:
                self.model_info = {
                    'source': 'local',
                    'model_path': model_path,
                    'vectorizer_path': vectorizer_path,
                    'loaded_at': datetime.now().isoformat(),
                    'model_type': type(self.model).__name__
                }
                self.last_loaded = datetime.now()
                return True
            
            return await self._load_dummy_model()
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo local: {e}")
            return await self._load_dummy_model()
    
    async def _load_dummy_model(self) -> bool:
        """
        Carrega um modelo dummy para desenvolvimento/teste.
        """
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np
            
            logger.warning("Carregando modelo dummy para desenvolvimento")
            
            # Cria modelo dummy
            self.model = LogisticRegression()
            self.vectorizer = TfidfVectorizer(max_features=100)
            
            # Treina com dados dummy
            dummy_texts = ["This is real news", "This is fake news", "Another real story"]
            dummy_labels = [0, 1, 0]
            
            X_dummy = self.vectorizer.fit_transform(dummy_texts)
            self.model.fit(X_dummy, dummy_labels)
            
            self.model_info = {
                'source': 'dummy',
                'loaded_at': datetime.now().isoformat(),
                'model_type': 'DummyLogisticRegression',
                'warning': 'Este é um modelo dummy para desenvolvimento'
            }
            
            self.last_loaded = datetime.now()
            logger.warning("Modelo dummy carregado - apenas para desenvolvimento!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar modelo dummy: {e}")
            return False
    
    def is_model_loaded(self) -> bool:
        """Verifica se o modelo está carregado."""
        return self.model is not None and self.vectorizer is not None
    
    def predict(self, text: str) -> Dict[str, Any]:
        """
        Faz predição para um texto.
        
        Args:
            text: Texto da notícia
            
        Returns:
            Dict com predição, confiança e probabilidades
        """
        if not self.is_model_loaded():
            raise RuntimeError("Modelo não está carregado")
        
        try:
            # Vectoriza texto
            text_vectorized = self.vectorizer.transform([text])
            
            # Predição
            prediction = self.model.predict(text_vectorized)[0]
            probabilities = self.model.predict_proba(text_vectorized)[0]
            
            # Mapeia predição
            prediction_label = 'fake' if prediction == 1 else 'real'
            confidence = max(probabilities)
            
            return {
                'prediction': prediction_label,
                'confidence': float(confidence),
                'probabilities': {
                    'real': float(probabilities[0]),
                    'fake': float(probabilities[1])
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na predição: {e}")
            raise RuntimeError(f"Erro na predição: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo carregado."""
        if not self.is_model_loaded():
            return {"status": "no_model"}
        
        return {
            "status": "loaded",
            "info": self.model_info,
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None
        }
    
    async def reload_model(self) -> bool:
        """Recarrega o modelo do S3."""
        return await self.load_model()


# Função utilitária para criar ModelLoader
def create_model_loader(s3_endpoint="http://localhost:4566",
                       bucket_name="fake-news-models") -> ModelLoader:
    """
    Cria um ModelLoader com configuração padrão.
    
    Args:
        s3_endpoint: URL do LocalStack
        bucket_name: Nome do bucket
        
    Returns:
        Instância configurada do ModelLoader
    """
    s3_config = {
        'endpoint_url': s3_endpoint,
        'bucket_name': bucket_name,
        'model_key': 'models/best_model.joblib',
        'vectorizer_key': 'models/vectorizer.joblib'
    }
    
    return ModelLoader(s3_config)


if __name__ == "__main__":
    # Teste básico
    async def test_loader():
        loader = create_model_loader()
        success = await loader.load_model()
        
        if success:
            print("Modelo carregado com sucesso!")
            info = loader.get_model_info()
            print(f"Info do modelo: {info}")
            
            # Teste de predição
            if loader.is_model_loaded():
                result = loader.predict("This is a test news article")
                print(f"Resultado do teste: {result}")
        else:
            print("Falha ao carregar modelo")
    
    asyncio.run(test_loader())