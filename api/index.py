import sys
import os

# Adiciona o diretório raiz ao PATH do Python no Serverless
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Exporta para a Vercel
app = app