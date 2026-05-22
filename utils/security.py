import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# Usamos a mesma chave do JWT para simplificar as variáveis de ambiente
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "uma-chave-secreta-para-dev")
s = URLSafeTimedSerializer(SECRET_KEY)

def generate_reset_token(email):
    return s.dumps(email, salt="reset-password")

def verify_reset_token(token, max_age=3600):
    """Retorna o e-mail se o token for válido (dentro de 1 hora)"""
    try:
        email = s.loads(token, salt="reset-password", max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None