import os
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

from routes.auth import auth_bp
from routes.extratos import extratos_bp


app = Flask(__name__)

CORS(
    app, 
    resources={r"/api/*": {"origins": "*"}},
    expose_headers=["Content-Disposition"]
    )

# Configuração do JWT (Token de Autenticação)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12) 
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
app.config['JWT_QUERY_STRING_NAME'] = 'jwt'
jwt = JWTManager(app)


app.register_blueprint(auth_bp)
app.register_blueprint(extratos_bp)


@app.route('/')
def index():
    return {"status": "ok", "mensagem": "API do Sistema Fiscal rodando!"}


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)