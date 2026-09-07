"""Persistencia da API em Firestore (Firebase Admin)."""

import os
import firebase_admin
from firebase_admin import credentials, firestore

# Caminho para o arquivo de credenciais que você baixou do Firebase
CAMINHO_CREDS = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(CAMINHO_CREDS)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def obter_db():
    """Retorna a instancia do cliente do Firestore."""
    return db

def iniciar():
    """No Firestore nao e necessario criar tabelas manualmente."""
    pass