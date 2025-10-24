# 🕵️ Detector de Fake News com Análise de Fairness

Este projeto implementa um sistema completo de detecção de fake news com foco especial em análise de fairness, utilizando os datasets FakeBR e FakeRecogna. O sistema inclui uma API REST, armazenamento em S3 (LocalStack), tracking de experimentos com MLflow e pipelines de CI/CD.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação e Setup](#instalação-e-setup)
- [Como Usar](#como-usar)
- [Análise de Fairness](#análise-de-fairness)
- [API](#api)
- [Docker e LocalStack](#docker-e-localstack)
- [CI/CD](#cicd)
- [Contribuição](#contribuição)

## 🎯 Visão Geral

Este projeto implementa um detector de fake news com as seguintes características:

- **Datasets**: FakeBR e FakeRecogna
- **Métricas de Fairness**: Demographic Parity Index (DI) e Statistical Parity Difference (SPD)
- **API REST**: FastAPI para servir predições
- **Armazenamento**: S3 simulado via LocalStack
- **Tracking**: MLflow para experimentos
- **CI/CD**: GitHub Actions com testes automatizados
- **Containerização**: Docker para deploy

## 📁 Estrutura do Projeto

```
fake-news-detector/
├── data/
│   ├── raw/                # Datasets originais (não versionados)
│   ├── processed/          # Datasets limpos/padronizados
│   └── reports/            # Gráficos DI/SPD e tabelas do relatório
├── notebooks/
│   ├── 01_preprocess_fakebr.ipynb       # Pré-processamento FakeBR
│   ├── 02_preprocess_fakerecogna.ipynb  # Pré-processamento FakeRecogna
│   ├── 03_fairness_analysis.ipynb       # Análise DI/SPD
│   └── 04_model_training.ipynb          # Treino e export de modelos
├── src/
│   ├── model/
│   │   ├── train.py                     # Scripts de treinamento
│   │   └── evaluate.py                  # Métricas e avaliação
│   ├── storage/
│   │   └── s3_client.py                 # Integração com LocalStack S3
│   └── api/
│       ├── app.py                       # FastAPI application
│       └── model_loader.py              # Carregamento de modelos do S3
├── docker/
│   ├── Dockerfile.api                   # Container da API
│   ├── docker-compose.yml               # Orquestração completa
│   └── localstack_bootstrap.sh          # Setup automático do S3
├── .github/
│   └── workflows/
│       └── ci.yml                       # Pipeline CI/CD
├── requirements.txt
├── .gitignore
└── README.md
```

## 🚀 Instalação e Setup

### Pré-requisitos

- Python 3.8+
- Docker e Docker Compose
- Git

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/fake-news-detector.git
cd fake-news-detector
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o ambiente com Docker

```bash
# Inicia todos os serviços (LocalStack, MLflow, API, Jupyter)
cd docker
docker-compose up -d

# Verifica se os serviços estão rodando
docker-compose ps
```

### 4. Acesse os serviços

- **API**: http://localhost:8000
- **MLflow**: http://localhost:5000
- **Jupyter**: http://localhost:8888 (token: `fake-news-dev`)
- **LocalStack S3**: http://localhost:4566

## 💻 Como Usar

### 1. Processamento dos Datasets

Execute os notebooks na ordem:

1. `01_preprocess_fakebr.ipynb` - Processa o dataset FakeBR
2. `02_preprocess_fakerecogna.ipynb` - Processa o FakeRecogna
3. `04_model_training.ipynb` - Treina os modelos

### 2. Análise de Fairness

Execute o notebook `03_fairness_analysis.ipynb` para:

- Calcular métricas DI (Demographic Parity Index)
- Calcular métricas SPD (Statistical Parity Difference)
- Gerar visualizações para o relatório
- Salvar resultados em `data/reports/`

### 3. Usando a API

```python
import requests

# Teste de saúde
response = requests.get("http://localhost:8000/health")
print(response.json())

# Predição individual
text = "Esta é uma notícia sobre política"
response = requests.post(
    "http://localhost:8000/predict",
    json={"text": text}
)
print(response.json())
```

### 4. Usando via linha de comando

```bash
# Treino de modelo
python src/model/train.py

# Avaliação
python src/model/evaluate.py

# Teste da API
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"text": "Exemplo de notícia para análise"}'
```

## 📊 Análise de Fairness

O projeto implementa duas métricas principais de fairness:

### Demographic Parity Index (DI)
- **Fórmula**: DI = min(P(Ŷ=1|A=a)) / max(P(Ŷ=1|A=a))
- **Interpretação**: Valores próximos a 1.0 indicam maior fairness
- **Uso**: Mede se diferentes grupos recebem predições positivas em taxas similares

### Statistical Parity Difference (SPD)
- **Fórmula**: SPD = |P(Ŷ=1|A=privileged) - P(Ŷ=1|A=unprivileged)|
- **Interpretação**: Valores próximos a 0.0 indicam maior fairness
- **Uso**: Mede a diferença absoluta nas taxas de predições positivas

### Visualizações Geradas

- Gráficos de barras comparando DI/SPD entre modelos
- Distribuições de predições por grupo sensível
- Matrizes de confusão segmentadas
- Relatórios de fairness exportados para `data/reports/`

## 🌐 API

### Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Health check básico |
| `/health` | GET | Status detalhado da API |
| `/predict` | POST | Predição individual |
| `/batch_predict` | POST | Predição em lote |
| `/model/info` | GET | Informações do modelo |
| `/model/reload` | POST | Recarrega modelo do S3 |

### Exemplo de Uso

```python
# Predição individual
{
  "text": "Notícia para análise"
}

# Resposta
{
  "prediction": "real",
  "confidence": 0.87,
  "probabilities": {
    "real": 0.87,
    "fake": 0.13
  }
}
```

## 🐳 Docker e LocalStack

### Serviços Incluídos

- **fake-news-api**: API FastAPI
- **localstack**: Simulação do AWS S3
- **mlflow**: Tracking de experimentos
- **jupyter**: Ambiente de desenvolvimento

### Comandos Úteis

```bash
# Inicia todos os serviços
docker-compose up -d

# Logs da API
docker-compose logs fake-news-api

# Acessa container da API
docker-compose exec fake-news-api bash

# Para todos os serviços
docker-compose down

# Rebuild da API
docker-compose build fake-news-api
```

### LocalStack S3

O LocalStack simula o AWS S3 localmente:

```bash
# Configurar AWS CLI para LocalStack
aws configure set aws_access_key_id test
aws configure set aws_secret_access_key test
aws configure set default.region us-east-1

# Listar modelos
aws --endpoint-url=http://localhost:4566 s3 ls s3://fake-news-models/models/

# Upload manual de modelo
aws --endpoint-url=http://localhost:4566 s3 cp model.joblib s3://fake-news-models/models/
```

## 🔄 CI/CD

O pipeline GitHub Actions inclui:

### Testes
- **Unit tests**: pytest com coverage
- **Lint**: flake8, black, isort
- **Security**: bandit, safety
- **Notebooks**: nbval para validação

### Build e Deploy
- **Docker build**: Constrói imagem da API
- **Integration tests**: Testa com LocalStack
- **Security scanning**: Análise de vulnerabilidades

### Configuração

O pipeline é ativado automaticamente em:
- Push para `main` ou `develop`
- Pull requests para `main`

## 🤝 Contribuição

### Setup de Desenvolvimento

1. Fork o repositório
2. Crie uma branch para sua feature
3. Instale dependências de desenvolvimento:

```bash
pip install -r requirements.txt
pip install pre-commit
pre-commit install
```

4. Execute testes localmente:

```bash
pytest tests/ -v
flake8 src/
black --check src/
isort --check-only src/
```

### Guidelines

- Siga PEP 8 para código Python
- Adicione testes para novas funcionalidades
- Documente funções e classes
- Use type hints
- Atualize README se necessário

## 📈 Métricas e Monitoramento

### MLflow

- **Tracking URI**: http://localhost:5000
- **Experiments**: Comparação de modelos
- **Artifacts**: Modelos e gráficos
- **Metrics**: Accuracy, Precision, Recall, F1, DI, SPD

### Logs

- **API Logs**: Disponíveis via `docker-compose logs`
- **Model Performance**: Registrado no MLflow
- **Fairness Metrics**: Salvos em `data/reports/`

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# API
PORT=8000
HOST=0.0.0.0

# S3 (LocalStack)
S3_ENDPOINT=http://localhost:4566
S3_BUCKET=fake-news-models
MODEL_KEY=models/best_model.joblib
VECTORIZER_KEY=models/vectorizer.joblib

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
```

### Configuração Local

Crie um arquivo `.env` na raiz do projeto:

```env
S3_ENDPOINT=http://localhost:4566
S3_BUCKET=fake-news-models
MLFLOW_TRACKING_URI=http://localhost:5000
```

## 📚 Referências

- [FakeBR Dataset](https://github.com/roneysco/Fake.br-Corpus)
- [FakeRecogna Dataset](https://www.kaggle.com/datasets/ruchi798/fakerecogna)
- [Fairlearn Documentation](https://fairlearn.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LocalStack Documentation](https://docs.localstack.cloud/)
- [MLflow Documentation](https://mlflow.org/docs/)

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Contato

- **Autor**: [Seu Nome]
- **Email**: [seu-email@exemplo.com]
- **GitHub**: [seu-usuario]

---

**Nota**: Este é um projeto acadêmico com foco em análise de fairness em modelos de ML. Os dados dos datasets não estão incluídos no repositório devido ao tamanho e licenças específicas.