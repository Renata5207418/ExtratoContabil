import os
import sys
import io
import re
import json
import time
import unicodedata
from datetime import datetime
import fitz  
import cv2
import numpy as np
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from ofxparse import OfxParser

# ==========================================================
# SETUP
# ==========================================================
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
RAIZ_PROJETO = os.path.dirname(DIRETORIO_ATUAL)

if RAIZ_PROJETO not in sys.path:
    sys.path.append(RAIZ_PROJETO)

load_dotenv(os.path.join(RAIZ_PROJETO, ".env"))

try:
    from services.mongo import arquivos_col
except Exception:
    arquivos_col = None

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

MONEY_PATTERN = r"[+-]?\s*(?:R\$\s*)?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\s*(?:R\$\s*)?\d+,\d{2}"

# ==========================================================
# HELPERS DE METADADOS
# ==========================================================
def normalizar_texto(texto: str) -> str:
    if not texto: return ""
    texto = texto.replace("\xa0", " ")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower()

def valor_para_float(valor):
    if not valor: return None
    texto = str(valor).replace("\xa0", " ").replace("R$", "").replace("+", "").replace("-", "").strip()
    texto = re.sub(r"[^\d,\.]", "", texto).replace(".", "").replace(",", ".")
    try: return float(texto)
    except ValueError: return None

def detectar_instituicao(texto: str, nome_arquivo: str = ""):
    t = normalizar_texto(texto + " " + nome_arquivo)
    pistas = [
        ("Omie.CASH", ["omie.cash", "omie cash", "extrato de omie"]),
        ("Nubank", ["nubank", "nu pagamentos", "nu financeira"]),
        ("Transpocred", ["transpocred"]),
        ("Banco Inter", ["banco inter", "instituicao: banco inter"]),
        ("Banco do Brasil", ["banco do brasil", "bb ", "extrato de conta corrente"]),
        ("Caixa Econômica", ["sac caixa", "alo caixa", "caixa economica", "extrato por periodo"]),
        ("Itaú", ["itau", "itaú"]),
        ("Sicredi", ["sicredi"]),
        ("Bradesco", ["bradesco"]),
        ("Santander", ["santander"]),
        ("Sicoob", ["sicoob"]),
    ]
    for nome, termos in pistas:
        if any(termo in t for termo in termos): return nome
    return "Desconhecido"

def extrair_periodo(texto: str) -> str:
    t = normalizar_texto(texto)
    
    padroes = [
        r"periodo do extrato\s+(\d{2})\s*/\s*(\d{4})",
        r"periodo de:?\s+\d{2}/(\d{2})/(\d{4})",
        r"periodo:\s+\d{2}/(\d{2})/(\d{4})",
        r"lancamentos do periodo:\s+\d{2}/(\d{2})/(\d{4})",
        r"entre\s+\d{2}/(\d{2})/(\d{4})\s+e\s+\d{2}/\d{2}/\d{4}",
        r"\b\d{2}/(\d{2})/(\d{4})\s+(?:a|ate)\s+\d{2}/\d{2}/\d{4}\b",
    ]
    for padrao in padroes:
        match = re.search(padrao, t, re.IGNORECASE)
        if match: return f"{match.group(1)}/{match.group(2)}"
    
    meses = {"janeiro": "01", "fevereiro": "02", "marco": "03", "abril": "04", "maio": "05", "junho": "06", 
             "julho": "07", "agosto": "08", "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"}
    
    match_extenso = re.search(r"\d{1,2}\s+(?:de)\s+([a-z]+)\s+(?:de)\s+(\d{4})", t)
    if match_extenso and match_extenso.group(1) in meses:
        return f"{meses[match_extenso.group(1)]}/{match_extenso.group(2)}"
        
    match_curto = re.search(r"\b([a-z]+)/(\d{4})\b", t)
    if match_curto and match_curto.group(1) in meses:
         return f"{meses[match_curto.group(1)]}/{match_curto.group(2)}"
         
    return "Não identificado"

# ==========================================================
# EXTRAÇÃO OFX (100% DE PRECISÃO)
# ==========================================================
def processar_ofx(caminho_arquivo: str):
    try:
        with open(caminho_arquivo, "rb") as fileobj:
            ofx = OfxParser.parse(fileobj)

        conta = ofx.account
        extrato = conta.statement
        movimentacoes = []

        for tx in extrato.transactions:
            valor = float(tx.amount)
            movimentacoes.append({
                "data": tx.date.strftime("%d/%m/%Y"),
                "descricao": tx.memo or tx.payee or "Transação",
                "valor": abs(valor),
                "natureza": "entrada" if valor >= 0 else "saida"
            })

        return {
            "status_leitura": "ok",
            "mensagem_leitura": "Lido perfeitamente via OFX.",
            "banco": conta.routing_number or "Banco Desconhecido",
            "periodo": extrato.start_date.strftime("%m/%Y") if extrato.start_date else "Não identificado",
            "tipo_documento": "Extrato OFX",
            "resumo_estruturado": {
                "sem_movimento": False,
                "saldo_final": float(extrato.balance) if extrato.balance else 0.0,
                "movimentacoes_flat": movimentacoes
            }
        }
    except Exception as e:
        return {"status_leitura": "nao_legivel", "mensagem_leitura": f"Erro ao ler OFX: {e}"}

# ==========================================================
# EXTRAÇÃO PDF (MELHOR ESFORÇO)
# ==========================================================
def extrair_texto_pdf(caminho_pdf: str) -> str:
    texto = ""
    try:
        with fitz.open(caminho_pdf) as doc:
            for i in range(len(doc)):
                texto += "\n" + doc[i].get_text()
            
            if len(texto.strip()) < 100:
                print("  ↳ PDF escaneado. Rodando OCR...")
                texto_paginas = []
                for idx in range(len(doc)):
                    pix = doc[idx].get_pixmap(dpi=300)
                    img_cv = np.array(Image.open(io.BytesIO(pix.tobytes("png"))).convert("L"))
                    bin_img = cv2.adaptiveThreshold(img_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
                    texto_paginas.append(pytesseract.image_to_string(bin_img, lang="por+eng", config="--oem 3 --psm 3"))
                texto = "\n".join(texto_paginas)
        return re.sub(r"[ \t]{2,}", " ", texto).strip()
    except Exception:
        return ""

def tentar_extrair_transacoes_pdf(linhas):
    movimentacoes = []
    buffer_tx = {}
    padrao_data = re.compile(r"^(\d{2}/\d{2}/\d{4})")
    
    try:
        for linha in linhas:
            linha_limpa = linha.strip()
            
            match_data = padrao_data.search(linha_limpa)
            if match_data:
                if buffer_tx.get("data") and buffer_tx.get("valor") is not None:
                    movimentacoes.append(buffer_tx)
                buffer_tx = {"data": match_data.group(1), "descricao": "", "valor": None, "natureza": "saida"}
                continue
                
            if not buffer_tx.get("data"):
                continue

            match_valor = re.search(rf"^(?:{MONEY_PATTERN})\s+([CDcd])$", linha_limpa)
            if match_valor and buffer_tx["valor"] is None:
                buffer_tx["valor"] = valor_para_float(linha_limpa)
                buffer_tx["natureza"] = "entrada" if match_valor.group(1).upper() == "C" else "saida"
                continue
            
            match_misto = re.search(rf"(.+?)\s+(?:{MONEY_PATTERN})\s+([CDcd])?$", linha_limpa)
            if match_misto and buffer_tx["valor"] is None:
                valores = re.findall(rf"(?:{MONEY_PATTERN})", linha_limpa)
                if valores:
                    buffer_tx["valor"] = valor_para_float(valores[0])
                    if match_misto.group(2):
                        buffer_tx["natureza"] = "entrada" if match_misto.group(2).upper() == "C" else "saida"
                continue

    except Exception as e:
        print(f"  ↳ Aviso: Falha na extração de transações ({e}). Salvando apenas metadados.")
        return []
        
    return movimentacoes

def processar_pdf(caminho_arquivo: str, nome_arquivo: str):
    texto = extrair_texto_pdf(caminho_arquivo)
    if not texto:
        return {"status_leitura": "nao_legivel", "mensagem_leitura": "PDF sem texto ou ilegível."}

    banco = detectar_instituicao(texto, nome_arquivo)
    periodo = extrair_periodo(texto)
    
    sem_movimento = any(x in normalizar_texto(texto) for x in ["nenhuma movimentacao", "sem lancamentos", "nao houve movimentacoes"])

    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    movimentacoes = [] if sem_movimento else tentar_extrair_transacoes_pdf(linhas)

    # Lógica de Auditoria: Se achou banco e período, o arquivo é válido.
    if banco != "Desconhecido" and periodo != "Não identificado":
        status = "ok" if (movimentacoes or sem_movimento) else "revisar"
        mensagem = "Leitura completa." if status == "ok" else "Metadados extraídos. Transações requerem revisão manual."
        
        return {
            "status_leitura": status,
            "mensagem_leitura": mensagem,
            "banco": banco,
            "periodo": periodo,
            "tipo_documento": "Extrato Bancário",
            "resumo_estruturado": {
                "sem_movimento": sem_movimento,
                "movimentacoes_flat": movimentacoes
            }
        }
    else:
        return {
            "status_leitura": "nao_legivel",
            "mensagem_leitura": "Não foi possível identificar o Banco ou o Período de competência.",
            "banco": banco,
            "periodo": periodo,
            "tipo_documento": "Desconhecido"
        }

# ==========================================================
# ORQUESTRADOR
# ==========================================================
def processar_lote_documentos():
    if arquivos_col is None:
        print("[x] Mongo não configurado. Use o teste.py para rodar localmente.")
        return

    pendentes = list(arquivos_col.find({"status": "pendente"}))
    if not pendentes:
        print("\n[✓] Nenhum documento pendente.")
        return

    print(f"\n=== Processando {len(pendentes)} documentos ===\n")

    for arq in pendentes:
        caminho = arq.get("caminho_completo", "")
        nome = arq.get("nome_arquivo", "Desconhecido")
        _id = arq["_id"]

        print(f"Lendo: {nome}...")

        if not os.path.exists(caminho):
            arquivos_col.update_one({"_id": _id}, {"$set": {"status": "nao_legivel", "mensagem_leitura": "Arquivo não encontrado."}})
            continue

        if nome.lower().endswith(".ofx"):
            dados = processar_ofx(caminho)
        else:
            dados = processar_pdf(caminho, nome)

        db_status = "processado" if dados.get("status_leitura") == "ok" else \
                    "processado_com_alerta" if dados.get("status_leitura") == "revisar" else "nao_legivel"

        arquivos_col.update_one({"_id": _id}, {
            "$set": {
                "tipo_documento": dados.get("tipo_documento", "Desconhecido"),
                "banco": dados.get("banco", "Desconhecido"),
                "periodo": dados.get("periodo", "N/A"),
                "status": db_status,
                "status_leitura": dados.get("status_leitura"),
                "mensagem_leitura": dados.get("mensagem_leitura"),
                "conteudo": json.dumps(dados.get("resumo_estruturado", {}), ensure_ascii=False),
                "data_processamento": datetime.now(),
            }
        })
        print(f"  [✓] Status: {db_status}")

if __name__ == "__main__":
    processar_lote_documentos()

    