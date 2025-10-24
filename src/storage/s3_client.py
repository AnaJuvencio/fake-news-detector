"""
Cliente S3 para integração com LocalStack.
Este módulo fornece uma interface para interagir com o serviço S3 simulado
via LocalStack para armazenar e recuperar modelos treinados.
"""

import boto3
import os
import joblib
from botocore.exceptions import ClientError, NoCredentialsError
import tempfile
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Client:
    """Cliente para interação com S3 (LocalStack)."""
    
    def __init__(self, 
                 endpoint_url="http://localhost:4566",  # LocalStack default
                 aws_access_key_id="test",
                 aws_secret_access_key="test",
                 region_name="us-east-1"):
        """
        Inicializa cliente S3 para LocalStack.
        
        Args:
            endpoint_url: URL do LocalStack (padrão: http://localhost:4566)
            aws_access_key_id: Chave de acesso (fake para LocalStack)
            aws_secret_access_key: Chave secreta (fake para LocalStack)
            region_name: Região AWS (padrão: us-east-1)
        """
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )
            logger.info(f"Cliente S3 inicializado com endpoint: {endpoint_url}")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente S3: {e}")
            raise
    
    def create_bucket(self, bucket_name):
        """Cria um bucket S3."""
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' criado com sucesso.")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyExists':
                logger.info(f"Bucket '{bucket_name}' já existe.")
                return True
            else:
                logger.error(f"Erro ao criar bucket: {e}")
                return False
    
    def upload_model(self, model_object, bucket_name, object_key):
        """
        Faz upload de um modelo (objeto Python) para S3.
        
        Args:
            model_object: Objeto do modelo (ex: sklearn model)
            bucket_name: Nome do bucket
            object_key: Chave/caminho do objeto no S3
        """
        try:
            # Salva modelo em arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp_file:
                joblib.dump(model_object, tmp_file.name)
                tmp_file_path = tmp_file.name
            
            # Upload para S3
            self.s3_client.upload_file(tmp_file_path, bucket_name, object_key)
            
            # Remove arquivo temporário
            os.unlink(tmp_file_path)
            
            logger.info(f"Modelo carregado para s3://{bucket_name}/{object_key}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao fazer upload do modelo: {e}")
            return False
    
    def download_model(self, bucket_name, object_key, local_path=None):
        """
        Faz download de um modelo do S3 e o carrega em memória.
        
        Args:
            bucket_name: Nome do bucket
            object_key: Chave/caminho do objeto no S3
            local_path: Caminho local opcional para salvar o arquivo
        
        Returns:
            Objeto do modelo carregado
        """
        try:
            if local_path is None:
                # Usa arquivo temporário
                with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp_file:
                    local_path = tmp_file.name
                    
            # Download do S3
            self.s3_client.download_file(bucket_name, object_key, local_path)
            
            # Carrega modelo
            model = joblib.load(local_path)
            
            # Remove arquivo temporário se foi criado aqui
            if local_path.startswith(tempfile.gettempdir()):
                os.unlink(local_path)
            
            logger.info(f"Modelo baixado de s3://{bucket_name}/{object_key}")
            return model
            
        except Exception as e:
            logger.error(f"Erro ao fazer download do modelo: {e}")
            return None
    
    def list_models(self, bucket_name, prefix="models/"):
        """Lista todos os modelos no bucket."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                models = [obj['Key'] for obj in response['Contents']]
                logger.info(f"Encontrados {len(models)} modelos no bucket '{bucket_name}'")
                return models
            else:
                logger.info(f"Nenhum modelo encontrado no bucket '{bucket_name}' com prefixo '{prefix}'")
                return []
                
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {e}")
            return []
    
    def delete_model(self, bucket_name, object_key):
        """Remove um modelo do S3."""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            logger.info(f"Modelo removido: s3://{bucket_name}/{object_key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover modelo: {e}")
            return False
    
    def check_connection(self):
        """Verifica se a conexão com S3 está funcionando."""
        try:
            self.s3_client.list_buckets()
            logger.info("Conexão com S3 OK")
            return True
        except Exception as e:
            logger.error(f"Erro de conexão com S3: {e}")
            return False


# Função utilitária para configuração rápida
def get_s3_client(localstack_url="http://localhost:4566"):
    """Retorna um cliente S3 configurado para LocalStack."""
    return S3Client(endpoint_url=localstack_url)


if __name__ == "__main__":
    # Teste básico
    try:
        client = get_s3_client()
        if client.check_connection():
            print("Cliente S3 configurado com sucesso!")
        else:
            print("Falha na configuração do cliente S3")
    except Exception as e:
        print(f"Erro: {e}")