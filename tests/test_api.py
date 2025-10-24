"""
Testes para a API de detecção de fake news.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os

# Adiciona src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from api.app import app
    from api.model_loader import ModelLoader
except ImportError:
    pytest.skip("API dependencies not available", allow_module_level=True)


class TestAPI:
    """Classe de testes para a API."""
    
    @pytest.fixture
    def client(self):
        """Cliente de teste FastAPI."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Testa endpoint raiz."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_health_endpoint(self, client):
        """Testa endpoint de health check."""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # Pode não ter modelo carregado
        data = response.json()
        assert "status" in data
        assert "message" in data
    
    def test_predict_endpoint_without_model(self, client):
        """Testa predição sem modelo carregado."""
        response = client.post(
            "/predict",
            json={"text": "This is a test news article"}
        )
        # Pode retornar 503 se modelo não estiver carregado
        assert response.status_code in [200, 503]
    
    def test_predict_endpoint_empty_text(self, client):
        """Testa predição com texto vazio."""
        response = client.post(
            "/predict",
            json={"text": ""}
        )
        assert response.status_code == 400
    
    def test_model_info_endpoint(self, client):
        """Testa endpoint de informações do modelo."""
        response = client.get("/model/info")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestModelLoader:
    """Testes para o carregador de modelos."""
    
    @pytest.fixture
    def model_config(self):
        """Configuração de teste para o modelo."""
        return {
            'endpoint_url': 'http://localhost:4566',
            'bucket_name': 'test-bucket',
            'model_key': 'test-model.joblib',
            'vectorizer_key': 'test-vectorizer.joblib'
        }
    
    def test_model_loader_init(self, model_config):
        """Testa inicialização do ModelLoader."""
        loader = ModelLoader(model_config)
        assert loader.s3_config == model_config
        assert loader.model is None
        assert loader.vectorizer is None
    
    @pytest.mark.asyncio
    async def test_load_dummy_model(self, model_config):
        """Testa carregamento de modelo dummy."""
        loader = ModelLoader(model_config)
        # Força carregamento do modelo dummy
        success = await loader._load_dummy_model()
        assert success is True
        assert loader.is_model_loaded() is True
        assert loader.model_info['source'] == 'dummy'
    
    @pytest.mark.asyncio
    async def test_predict_with_dummy_model(self, model_config):
        """Testa predição com modelo dummy."""
        loader = ModelLoader(model_config)
        await loader._load_dummy_model()
        
        result = loader.predict("This is a test news article")
        assert 'prediction' in result
        assert 'confidence' in result
        assert 'probabilities' in result
        assert result['prediction'] in ['real', 'fake']
        assert 0 <= result['confidence'] <= 1