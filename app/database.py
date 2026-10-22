import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Configuração de Logs para depurar no painel da Vercel
logger = logging.getLogger("uvicorn.error")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

supabase: Client = None

# Tenta inicializar o cliente de forma segura sem derrubar a aplicação no Build
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL.startswith("http"):
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Cliente Supabase inicializado com sucesso!")
    except Exception as e:
        logger.error(f"Falha ao conectar no Supabase: {str(e)}")
        supabase = None
else:
    logger.warning("Variáveis SUPABASE_URL e/ou SUPABASE_KEY ausentes ou inválidas.")