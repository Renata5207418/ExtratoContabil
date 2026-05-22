import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv


# =========================
# CARREGAR .ENV DA RAIZ
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


def get_env_required(nome: str) -> str:
    valor = os.getenv(nome)

    if valor is None or str(valor).strip() == "":
        raise RuntimeError(f"Variável de ambiente obrigatória não configurada: {nome}")

    return str(valor).strip()


def montar_conn_str() -> str:
    driver = os.getenv("DOMINIO_ODBC_DRIVER", "SQL Anywhere 17").strip()

    host = get_env_required("DOMINIO_HOST")
    port = get_env_required("DOMINIO_PORT")
    dbname = get_env_required("DOMINIO_DB")
    user = get_env_required("DOMINIO_USER")
    password = get_env_required("DOMINIO_PASSWORD")

    # Se DOMINIO_ENGINE não estiver no .env, usa o host como fallback.
    eng = os.getenv("DOMINIO_ENGINE", "").strip() or host

    conn_str = (
        f"DRIVER={driver};"
        f"UID={user};"
        f"PWD={password};"
        f"ENG={eng};"
        f"DBN={dbname};"
        f"LINKS=TCPIP(HOST={host}:{port});"
    )

    return conn_str


def debug_conexao_sem_senha():
    """
    Mostra os dados carregados do .env sem expor senha.
    Use temporariamente para validar se o .env está sendo lido corretamente.
    """
    driver = os.getenv("DOMINIO_ODBC_DRIVER", "SQL Anywhere 17")
    host = os.getenv("DOMINIO_HOST")
    port = os.getenv("DOMINIO_PORT")
    dbname = os.getenv("DOMINIO_DB")
    user = os.getenv("DOMINIO_USER")
    eng = os.getenv("DOMINIO_ENGINE") or host

    print("=== DEBUG CONEXÃO DOMÍNIO ===")
    print(f"ENV_PATH: {ENV_PATH}")
    print(f"ENV existe? {ENV_PATH.exists()}")
    print(f"DRIVER: {driver}")
    print(f"HOST: {host}")
    print(f"PORT: {port}")
    print(f"DBN: {dbname}")
    print(f"ENG: {eng}")
    print(f"USER: {user}")
    print("=============================")


def get_cnpj_dominio(codigo_empresa: int) -> str:
    """Consulta rápida na Domínio para pegar o CNPJ pelo código."""
    try:
        conn_str = montar_conn_str()

        with pyodbc.connect(conn_str, timeout=5) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT cgce_emp
                    FROM bethadba.geempre
                    WHERE codi_emp = ?
                    """,
                    (codigo_empresa,)
                )

                row = cursor.fetchone()
                return row[0].strip() if row and row[0] else ""

    except Exception as e:
        print(f"Não foi possível consultar CNPJ na Domínio para empresa {codigo_empresa}: {e}")
        return ""


def get_todas_empresas_dominio() -> list:
    """Busca todas as empresas cadastradas na Domínio."""
    try:
        conn_str = montar_conn_str()

        with pyodbc.connect(conn_str, timeout=5) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT codi_emp, cgce_emp, nome_emp, stat_emp
                    FROM bethadba.geempre
                    WHERE codi_emp <= 4000
                    AND stat_emp = 'A'
                    ORDER BY codi_emp
                    """
                )

                rows = cursor.fetchall()

                empresas = []

                for row in rows:
                    empresas.append({
                        "codigo_dominio": row[0],
                        "cnpj": row[1].strip() if row[1] else "",
                        "nome_empresa": row[2].strip() if row[2] else ""
                    })

                return empresas

    except Exception as e:
        print(f"Erro ao buscar empresas na Domínio: {e}")
        return []


if __name__ == "__main__":
    debug_conexao_sem_senha()

    empresas = get_todas_empresas_dominio()
    print(f"Empresas encontradas: {len(empresas)}")

    if empresas:
        print(empresas[0])