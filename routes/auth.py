from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import datetime
from services.mongo import usuarios_col
from utils.security import generate_reset_token, verify_reset_token
from utils.email import send_reset_email


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ==== LOGIN ====
@auth_bp.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    
    if not dados or not dados.get('email') or not dados.get('password'):
        return jsonify({"erro": "E-mail e senha são obrigatórios."}), 400

    email = dados['email'].strip().lower()
    password = dados['password']

    user = usuarios_col.find_one({
        "$or": [
            {"email": email},
            {"username": {"$regex": f"^{email}$", "$options": "i"}}
        ]
    })

    if user and check_password_hash(user['senha_hash'], password):
        # Cria um token JWT contendo o ID e o email do usuário
        access_token = create_access_token(identity=str(user['_id']), additional_claims={"email": user['email']})
        
        return jsonify({
            "mensagem": "Login realizado com sucesso",
            "token": access_token,
            "usuario": {
                "username": user.get('username'),
                "email": user.get('email')
            }
        }), 200

    return jsonify({"erro": "Credenciais inválidas."}), 401


# ==== SOLICITAÇÃO DE RESET ====
@auth_bp.route('/reset-request', methods=['POST'])
def reset_request():
    dados = request.get_json()
    email = dados.get('email', '').strip().lower()
    
    user = usuarios_col.find_one({'email': email})
    
    if user:
        token = generate_reset_token(email)
        send_reset_email(email, token)
        
    return jsonify({"mensagem": "Se o e-mail existir em nossa base, as instruções foram enviadas."}), 200


# ==== CONFIRMAR RESET (Nova Senha) ====
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    dados = request.get_json()
    token = dados.get('token')
    nova_senha = dados.get('password')

    if not token or not nova_senha:
        return jsonify({"erro": "Token e nova senha são obrigatórios."}), 400

    email = verify_reset_token(token)
    if not email:
        return jsonify({"erro": "Token inválido ou expirado."}), 401

    senha_hash = generate_password_hash(nova_senha)
    usuarios_col.update_one({'email': email}, {'$set': {'senha_hash': senha_hash}})
    
    return jsonify({"mensagem": "Senha redefinida com sucesso!"}), 200


# ==== CADASTRO (REGISTRO) ====
@auth_bp.route('/register', methods=['POST'])
def register():
    dados = request.get_json()
    username = dados.get('username')
    email = dados.get('email', '').strip().lower()
    password = dados.get('password')

    if not username or not email or not password:
        return jsonify({"erro": "Todos os campos são obrigatórios."}), 400

    # Verifica se o usuário já existe
    if usuarios_col.find_one({'email': email}):
        return jsonify({"erro": "Este e-mail já está cadastrado."}), 400

    # Cria o hash da senha antes de salvar
    senha_hash = generate_password_hash(password)
    
    novo_usuario = {
        'username': username,
        'email': email,
        'senha_hash': senha_hash,
        'data_criacao': datetime.now()
    }
    
    usuarios_col.insert_one(novo_usuario)
    
    return jsonify({"mensagem": "Usuário criado com sucesso!"}), 201
