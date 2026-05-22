import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[MONGO_DB]

# Coleções
usuarios_col = db["usuarios"]
clientes_col = db["clientes"]
solicitacoes_col = db["solicitacoes"]
arquivos_col = db["arquivos"]