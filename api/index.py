import sys
import os

# Adiciona o diretório raiz do projeto ao PATH do Python no Serverless da Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Exporta a instância para o runtime ASGI da Vercel
app = app