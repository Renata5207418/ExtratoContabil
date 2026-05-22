import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "host": os.getenv("DOMINIO_HOST"),
    "port": os.getenv("DOMINIO_PORT"),
    "dbname": os.getenv("DOMINIO_DB"),
    "user": os.getenv("DOMINIO_USER"),
    "password": os.getenv("DOMINIO_PASSWORD"),
    "eng": os.getenv("DOMINIO_ENGINE"),
}

def get_cnpj_dominio(codigo_empresa: int) -> str:
    """Consulta rápida na Domínio para pegar o CNPJ pelo código."""
    try:
        conn_str = (
            "DRIVER=SQL Anywhere 17;"
            f"UID={DB_PARAMS['user']};"
            f"PWD={DB_PARAMS['password']};"
            f"ENG={DB_PARAMS['eng']};"
            f"DBN={DB_PARAMS['dbname']};"
            f"LINKS=TCPIP(host={DB_PARAMS['host']}:{DB_PARAMS['port']});"
        )
        with pyodbc.connect(conn_str, timeout=5) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT cgce_emp FROM bethadba.geempre WHERE codi_emp = ?", (codigo_empresa,))
                row = cursor.fetchone()
                return row[0].strip() if row else ""
    except Exception as e:
        print(f"Não foi possível consultar CNPJ na Domínio para empresa {codigo_empresa}: {e}")
        return ""

def get_todas_empresas_dominio() -> list:
    """Busca todas as empresas cadastradas na Domínio."""
    try:
        conn_str = (
            "DRIVER=SQL Anywhere 17;"
            f"UID={DB_PARAMS['user']};"
            f"PWD={DB_PARAMS['password']};"
            f"ENG={DB_PARAMS['eng']};"
            f"DBN={DB_PARAMS['dbname']};"
            f"LINKS=TCPIP(host={DB_PARAMS['host']}:{DB_PARAMS['port']});"
        )
        with pyodbc.connect(conn_str, timeout=5) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT codi_emp, cgce_emp, nome_emp FROM bethadba.geempre WHERE codi_emp <= 4000 ORDER BY codi_emp")
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