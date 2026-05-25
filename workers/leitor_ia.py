from __future__ import annotations

import os
import sys
import io
import re
import json
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ==========================================================
# SETUP DE CAMINHOS / ENV
# ==========================================================
DIRETORIO_ATUAL = Path(__file__).resolve().parent
RAIZ_PROJETO = DIRETORIO_ATUAL.parent

if str(RAIZ_PROJETO) not in sys.path:
    sys.path.append(str(RAIZ_PROJETO))

try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ_PROJETO / ".env")
except Exception:
    pass


# ==========================================================
# IMPORTS OPCIONAIS
# ==========================================================
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image
except Exception:
    cv2 = None
    np = None
    pytesseract = None
    Image = None

try:
    from ofxparse import OfxParser
except Exception:
    OfxParser = None

try:
    from services.mongo import arquivos_col
except Exception:
    arquivos_col = None


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================
USAR_OCR = os.getenv("LEITOR_IA_USAR_OCR", "1").strip().lower() not in {
    "0", "false", "nao", "não"
}

EXTENSOES_OFX = (".ofx", ".ofc", ".qfx")
EXTENSOES_PDF = (".pdf",)


if pytesseract is not None:
    try:
        if os.name == "nt":
            caminho_tesseract = os.getenv(
                "TESSERACT_CMD",
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            )
        else:
            caminho_tesseract = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")

        if caminho_tesseract and os.path.exists(caminho_tesseract):
            pytesseract.pytesseract.tesseract_cmd = caminho_tesseract
    except Exception:
        pass


# ==========================================================
# BASES SIMPLES DE IDENTIFICAÇÃO
# ==========================================================
MESES = {
    "janeiro": "01",
    "jan": "01",
    "fevereiro": "02",
    "fev": "02",
    "marco": "03",
    "março": "03",
    "mar": "03",
    "abril": "04",
    "abr": "04",
    "maio": "05",
    "mai": "05",
    "junho": "06",
    "jun": "06",
    "julho": "07",
    "jul": "07",
    "agosto": "08",
    "ago": "08",
    "setembro": "09",
    "set": "09",
    "outubro": "10",
    "out": "10",
    "novembro": "11",
    "nov": "11",
    "dezembro": "12",
    "dez": "12",
}

BANKID_PARA_BANCO = {
    "001": "Banco do Brasil",
    "1": "Banco do Brasil",
    "237": "Bradesco",
    "033": "Santander",
    "33": "Santander",
    "341": "Itaú",
    "104": "Caixa Econômica",
    "077": "Banco Inter",
    "77": "Banco Inter",
    "260": "Nubank",
    "336": "C6 Bank",
    "756": "Sicoob",
    "748": "Sicredi",
    "085": "Cooperativa / Ailos",
    "85": "Cooperativa / Ailos",
    "102": "XP Investimentos",
    "348": "XP Investimentos",
}

INSTITUICOES = [
    ("XP Investimentos", [
        "xp investimentos",
        "banco xp",
        "xp investimentos corretora",
        "corretora de cambio",
        "corretora de câmbio",
    ]),
    ("Omie.CASH", [
        "omie.cash",
        "omie cash",
        "conta omie",
        "extrato de omie",
    ]),
    ("Transpocred", [
        "transpocred",
        "sistema ailos",
    ]),
    ("Banco do Brasil", [
        "banco do brasil",
        "bb ",
        " bb",
    ]),
    ("Itaú", [
        "itauempresas",
        "itaúempresas",
        "banco itau",
        "banco itaú",
        "itau",
        "itaú",
    ]),
    ("Caixa Econômica", [
        "caixa economica",
        "caixa econômica",
        "sac caixa",
        "extrato por periodo",
        "extrato por período",
    ]),
    ("Banco Inter", [
        "banco inter",
        "instituicao: banco inter",
        "instituição: banco inter",
        "inter",
    ]),
    ("Nubank", [
        "nubank",
        "nu pagamentos",
        "nu financeira",
    ]),
    ("Bradesco", [
        "bradesco",
        "bradesco net empresa",
        "investimentos bradesco",
        "invest facil",
        "invest fácil",
    ]),
    ("Santander", [
        "santander",
    ]),
    ("Sicredi", [
        "sicredi",
    ]),
    ("Sicoob", [
        "sicoob",
    ]),
    ("C6 Bank", [
        "c6 bank",
        "banco c6",
    ]),
]


# ==========================================================
# REGEX GERAIS
# ==========================================================
RE_DATA_COMPLETA = re.compile(
    r"\b(\d{1,2})\s*[\/\-.]\s*(\d{1,2})\s*[\/\-.]\s*(\d{2,4})\b"
)

RE_INTERVALO_DATAS = re.compile(
    r"(\d{1,2})\s*[\/\-.]\s*(\d{1,2})\s*[\/\-.]\s*(\d{2,4})"
    r"\s*(?:a|ate|até|-)\s*"
    r"(\d{1,2})\s*[\/\-.]\s*(\d{1,2})\s*[\/\-.]\s*(\d{2,4})",
    re.IGNORECASE,
)

RE_VALOR_BR = re.compile(
    r"(?<!\d)(?:[+-]\s*)?(?:R\$\s*)?\d{1,3}(?:\.\d{3})*,\d{2}(?!\d)"
    r"|(?<!\d)(?:[+-]\s*)?(?:R\$\s*)?\d+,\d{2}(?!\d)",
    re.IGNORECASE,
)


# ==========================================================
# HELPERS
# ==========================================================
def normalizar_texto(texto: Any) -> str:
    if texto is None:
        return ""

    texto = str(texto).replace("\xa0", " ").replace("\ufeff", " ")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.lower()
    texto = re.sub(r"[\t\r\f\v]+", " ", texto)
    texto = re.sub(r" {2,}", " ", texto)
    return texto.strip()


def compactar_espacos(texto: Any) -> str:
    if texto is None:
        return ""
    return re.sub(r"\s+", " ", str(texto)).strip()


def somente_digitos(texto: Any) -> str:
    return re.sub(r"\D+", "", str(texto or ""))


def formatar_periodo(mes: Any, ano: Any) -> Optional[str]:
    try:
        mes_int = int(str(mes).strip())
        ano_int = int(str(ano).strip())

        if ano_int < 100:
            ano_int += 2000

        if not 1 <= mes_int <= 12:
            return None

        if not 1900 <= ano_int <= 2100:
            return None

        return f"{mes_int:02d}/{ano_int:04d}"
    except Exception:
        return None


def valor_para_float(valor: Any) -> Optional[float]:
    if valor is None:
        return None

    texto_original = (
        str(valor)
        .strip()
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
    )

    if not texto_original:
        return None

    sinal = -1 if "-" in texto_original else 1

    texto = texto_original.upper()
    texto = texto.replace("R$", "")
    texto = texto.replace("+", "")
    texto = texto.replace("-", "")
    texto = re.sub(r"[^\d,\.]", "", texto)

    if not texto:
        return None

    try:
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        return sinal * float(texto)
    except Exception:
        return None


def _json_default(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return ""


# ==========================================================
# EXTRAÇÃO DE TEXTO PDF
# ==========================================================
def _ocr_pdf_com_fitz(doc: Any) -> str:
    if not USAR_OCR:
        return ""

    if pytesseract is None or cv2 is None or np is None or Image is None:
        return ""

    textos_paginas: List[str] = []

    try:
        for idx in range(len(doc)):
            page = doc[idx]
            pix = page.get_pixmap(dpi=300)
            img_pil = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
            img_cv = np.array(img_pil)

            bin_img = cv2.adaptiveThreshold(
                img_cv,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                9,
            )

            texto_pag = pytesseract.image_to_string(
                bin_img,
                lang=os.getenv("TESSERACT_LANG", "por+eng"),
                config="--oem 3 --psm 3",
            )

            textos_paginas.append(texto_pag)
    except Exception:
        return ""

    return "\n".join(textos_paginas).strip()


def _extrair_texto_pdf_com_origem(caminho_pdf: str) -> Tuple[str, str]:
    if fitz is None:
        return "", "pdf_sem_pymupdf"

    texto = ""
    origem = "pdf_texto"

    try:
        with fitz.open(caminho_pdf) as doc:
            partes: List[str] = []

            for i in range(len(doc)):
                try:
                    partes.append(doc[i].get_text("text", sort=True))
                except Exception:
                    partes.append(doc[i].get_text())

            texto = "\n".join(partes).strip()

            if len(texto.strip()) < 100:
                texto_ocr = _ocr_pdf_com_fitz(doc)
                if texto_ocr:
                    texto = texto_ocr
                    origem = "pdf_ocr"

        texto = texto.replace("\xa0", " ").replace("\ufeff", " ")
        texto = re.sub(r"[ \t]{2,}", " ", texto)
        texto = re.sub(r"\n{3,}", "\n\n", texto)

        return texto.strip(), origem

    except Exception:
        return "", "pdf_erro"


def extrair_texto_pdf(caminho_pdf: str) -> str:
    texto, _origem = _extrair_texto_pdf_com_origem(caminho_pdf)
    return texto


# ==========================================================
# BANCO
# ==========================================================
def _normalizar_bankid(bank_id: Optional[str]) -> Optional[str]:
    if not bank_id:
        return None

    digitos = somente_digitos(bank_id)

    if not digitos:
        return None

    sem_zeros = digitos.lstrip("0") or "0"

    if digitos in BANKID_PARA_BANCO:
        return digitos

    if sem_zeros in BANKID_PARA_BANCO:
        return sem_zeros

    if len(digitos) >= 3 and digitos[-3:] in BANKID_PARA_BANCO:
        return digitos[-3:]

    return digitos


def detectar_instituicao_com_origem(
    texto: str,
    nome_arquivo: str = "",
    bank_id: Optional[str] = None,
) -> Tuple[str, str]:
    bankid_norm = _normalizar_bankid(bank_id)

    if bankid_norm and bankid_norm in BANKID_PARA_BANCO:
        return BANKID_PARA_BANCO[bankid_norm], "bankid"

    nome_norm = normalizar_texto(nome_arquivo)
    texto_norm = normalizar_texto(texto)

    for nome_banco, termos in INSTITUICOES:
        termos_norm = [normalizar_texto(t) for t in termos]

        if any(t and t in nome_norm for t in termos_norm):
            return nome_banco, "nome_arquivo"

    combinado = f"{texto_norm} {nome_norm}"

    for nome_banco, termos in INSTITUICOES:
        termos_norm = [normalizar_texto(t) for t in termos]

        if any(t and t in combinado for t in termos_norm):
            return nome_banco, "texto"

    return "Desconhecido", "nao_identificado"


def detectar_instituicao(texto: str, nome_arquivo: str = "") -> str:
    banco, _origem = detectar_instituicao_com_origem(texto, nome_arquivo)
    return banco


# ==========================================================
# PERÍODO
# ==========================================================
def _periodo_em_partes_do_caminho(caminho_arquivo: str) -> Optional[str]:
    """
    Prioriza o mês da pasta, exemplo:
    .../04.2026/36535/EXTRATO/arquivo.pdf

    Isso é importante porque alguns bancos geram extrato de 07/04 a 07/05,
    mas a solicitação pertence à pasta 04.2026.
    """
    if not caminho_arquivo:
        return None

    partes = re.split(r"[\\/]+", str(caminho_arquivo))

    for parte in partes:
        parte_norm = normalizar_texto(parte)
        m = re.fullmatch(
            r"(0?[1-9]|1[0-2])\s*[\.\-_]\s*(20\d{2}|19\d{2})",
            parte_norm,
        )
        if m:
            return formatar_periodo(m.group(1), m.group(2))

    return None


def extrair_periodo_nome_arquivo(nome_arquivo: str) -> Optional[str]:
    if not nome_arquivo:
        return None

    nome = normalizar_texto(nome_arquivo)

    # Intervalo de datas no nome:
    # Extrato-07-04-2026-a-07-05-2026.pdf
    # Para competência fiscal, usa a data inicial.
    m = RE_INTERVALO_DATAS.search(nome)
    if m:
        return formatar_periodo(m.group(2), m.group(3))

    # 04.2026 / 04-2026 / 04_2026 / 04/2026
    m = re.search(
        r"(?<!\d)(0?[1-9]|1[0-2])\s*[\.\-_\/]\s*(20\d{2}|19\d{2})(?!\d)",
        nome,
    )
    if m:
        return formatar_periodo(m.group(1), m.group(2))

    # 2026-04 / 2026_04
    m = re.search(
        r"(?<!\d)(20\d{2}|19\d{2})\s*[\.\-_\/]\s*(0?[1-9]|1[0-2])(?!\d)",
        nome,
    )
    if m:
        return formatar_periodo(m.group(2), m.group(1))

    # Abril 2026
    for mes_nome, mes_num in MESES.items():
        mes_norm = re.escape(normalizar_texto(mes_nome))
        padrao = rf"(?<![a-z]){mes_norm}(?![a-z])[^0-9a-z]*(20\d{{2}}|19\d{{2}})"
        m = re.search(padrao, nome)

        if m:
            return formatar_periodo(mes_num, m.group(1))

    return None


def extrair_periodo_texto(texto: str) -> Tuple[Optional[str], str]:
    if not texto:
        return None, "nao_identificado"

    t = normalizar_texto(texto)

    # Intervalo de datas no texto.
    # Para competência, usa a data inicial.
    m = RE_INTERVALO_DATAS.search(t)
    if m:
        periodo = formatar_periodo(m.group(2), m.group(3))
        if periodo:
            return periodo, "texto_intervalo_inicial"

    # "Período: 04/2026", "Competência 04/2026"
    m = re.search(
        r"\b(?:competencia|periodo|mes|mês)\s*[:\-]?\s*"
        r"(0?[1-9]|1[0-2])\s*/\s*(20\d{2}|19\d{2})\b",
        t,
        re.IGNORECASE,
    )
    if m:
        periodo = formatar_periodo(m.group(1), m.group(2))
        if periodo:
            return periodo, "texto_mes_ano"

    # Abril/2026 ou Abril de 2026
    for mes_nome, mes_num in MESES.items():
        mes_nome_norm = normalizar_texto(mes_nome)
        padroes = [
            rf"(?<![a-z]){re.escape(mes_nome_norm)}(?![a-z])\s*/\s*(20\d{{2}}|19\d{{2}})\b",
            rf"(?<![a-z]){re.escape(mes_nome_norm)}(?![a-z])\s+de\s+(20\d{{2}}|19\d{{2}})\b",
        ]

        for padrao in padroes:
            m = re.search(padrao, t, re.IGNORECASE)
            if m:
                periodo = formatar_periodo(mes_num, m.group(1))
                if periodo:
                    return periodo, "texto_mes_extenso"

    return None, "nao_identificado"


def extrair_periodo(
    texto: str = "",
    nome_arquivo: str = "",
    caminho_arquivo: str = "",
) -> Tuple[Optional[str], str]:
    periodo_pasta = _periodo_em_partes_do_caminho(caminho_arquivo)
    if periodo_pasta:
        return periodo_pasta, "pasta"

    periodo_nome = extrair_periodo_nome_arquivo(nome_arquivo)
    if periodo_nome:
        return periodo_nome, "nome_arquivo"

    return extrair_periodo_texto(texto)


# ==========================================================
# TIPO DO DOCUMENTO
# ==========================================================
def classificar_tipo_documento(texto: str, nome_arquivo: str = "", banco: str = "") -> str:
    t = normalizar_texto(f"{nome_arquivo}\n{texto}")

    # Borderô / relatório financeiro
    if any(x in t for x in [
        "bordero",
        "borderô",
        "relacao de creditos",
        "relacao do debito",
        "pagamentos e recebimentos",
        "saldos bancos saldo inicial entradas no dia",
    ]):
        return "Borderô / Relatório Financeiro"

    # Relatório de conciliação
    if any(x in t for x in [
        "conciliacao",
        "conciliação",
        "extrato sicredi rbm",
        "cliente/fornecedor historico categoria entrada saida",
        "historico categoria entrada saida saldo do dia",
        "diferenca entrada saida",
        "saldo do dia (s)",
    ]):
        return "Relatório de Conciliação"

    # Cotas / capital
    if any(x in t for x in [
        "extrato do capital",
        "extrato de capital",
        "cotas capitais",
        "cotas capital",
        "cr. cotas",
        "demonstrativo de capital",
        "movimentacao de capital social",
    ]):
        return "Extrato de Cotas/Capital"

    # Investimentos
    if any(x in t for x in [
        "extrato de investimentos",
        "xp investimentos",
        "cdb banco xp",
        "invest facil",
        "invest fácil",
        "valor resgate liquido",
        "valor resgate líquido",
        "valor resgate bruto",
        "valor renda bruta",
        "total de aplicacoes",
        "total de aplicações",
        "total de resgates",
        "fundos/clubes",
        "renda fixa",
        "aplicacao",
        "aplicação",
        "resgate",
        "cdb",
    ]):
        return "Extrato de Investimentos"

    # Extrato bancário comum
    if any(x in t for x in [
        "extrato bancario",
        "extrato bancário",
        "extrato de conta corrente",
        "consulta - extrato",
        "conta corrente",
        "saldo disponivel",
        "saldo disponível",
        "lancamentos",
        "lançamentos",
        "transacoes",
        "transações",
    ]):
        return "Extrato Bancário"

    if "extrato" in t:
        return "Extrato Bancário"

    return "Desconhecido"


# ==========================================================
# SEM MOVIMENTO / SALDO
# ==========================================================
def detectar_sem_movimento(texto: str) -> bool:
    """
    Regra semântica genérica, sem mapear frase por frase.

    Procura padrões como:
    - não há transações
    - não houve movimentações
    - nenhuma movimentação encontrada
    - sem lançamentos
    """
    if not texto:
        return False

    t = normalizar_texto(texto)

    padroes = [
        r"(?:nao\s+(?:ha|houve|existem?|foram\s+encontrad[ao]s?)|nenhum(?:a)?|sem)\s+[\w\s]{0,40}?(?:transacoes|transacao)",
        r"(?:nao\s+(?:ha|houve|existem?|foram\s+encontrad[ao]s?)|nenhum(?:a)?|sem)\s+[\w\s]{0,40}?(?:movimentacoes|movimentacao)",
        r"(?:nao\s+(?:ha|houve|existem?|foram\s+encontrad[ao]s?)|nenhum(?:a)?|sem)\s+[\w\s]{0,40}?(?:lancamentos|lancamento)",
    ]

    if any(re.search(padrao, t, re.IGNORECASE) for padrao in padroes):
        return True

    # Casos com totais zerados.
    tem_entrada_zero = re.search(r"total\s+de\s+entradas\s+0,00", t) is not None
    tem_saida_zero = re.search(r"total\s+de\s+saidas\s+0,00", t) is not None

    if tem_entrada_zero and tem_saida_zero:
        return True

    return False


def extrair_saldo_final_simples(texto: str) -> Optional[float]:
    """
    Campo opcional. Não define sucesso ou falha do leitor.
    """
    if not texto:
        return None

    t = normalizar_texto(texto)

    padroes = [
        r"saldo\s+final\s+do\s+periodo(?:\s*\([^)]*\))?\s*[:\-]?\s*(?:r\$\s*)?([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
        r"saldo\s+final\s*[:\-]?\s*(?:r\$\s*)?([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
        r"saldo\s+disponivel\s*[:\-]?\s*(?:r\$\s*)?([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
        r"saldo\s+total\s*(?:\(r\$\))?\s*[:\-]?\s*(?:r\$\s*)?([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
    ]

    for padrao in padroes:
        m = re.search(padrao, t, re.IGNORECASE)
        if m:
            return valor_para_float(m.group(1))

    return None


# ==========================================================
# CONFIANÇA / STATUS
# ==========================================================
def calcular_confianca_metadados(
    banco: str,
    periodo: Optional[str],
    tipo_documento: str,
    origem_banco: str,
    origem_periodo: str,
    sem_movimento: bool,
) -> float:
    pontos = 0.0

    if banco and banco != "Desconhecido":
        pontos += 0.35
        if origem_banco in {"texto", "nome_arquivo", "bankid"}:
            pontos += 0.10

    if periodo and periodo != "Não identificado":
        pontos += 0.35
        if origem_periodo in {"pasta", "nome_arquivo", "texto_intervalo_inicial", "texto_mes_ano", "ofx_dtend"}:
            pontos += 0.10

    if tipo_documento and tipo_documento != "Desconhecido":
        pontos += 0.05

    if sem_movimento:
        pontos += 0.05

    return round(max(0.0, min(0.99, pontos)), 2)


def montar_resultado(
    status_leitura: str,
    mensagem_leitura: str,
    banco: str,
    periodo: Optional[str],
    tipo_documento: str,
    confianca: float,
    origem_banco: str,
    origem_periodo: str,
    resumo: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "status_leitura": status_leitura,
        "mensagem_leitura": mensagem_leitura,
        "banco": banco or "Desconhecido",
        "periodo": periodo or "Não identificado",
        "tipo_documento": tipo_documento or "Desconhecido",
        "confianca": confianca,
        "origem_banco": origem_banco,
        "origem_periodo": origem_periodo,
        "resumo_estruturado": resumo,
    }


# ==========================================================
# OFX
# ==========================================================
def _ofx_get_tag(texto: str, tag: str) -> Optional[str]:
    padroes = [
        rf"<{tag}>\s*([^<\r\n]+)",
        rf"<{tag}>\s*(.*?)\s*</{tag}>",
    ]

    for padrao in padroes:
        m = re.search(padrao, texto, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return compactar_espacos(m.group(1))

    return None


def parse_data_ofx(valor: Optional[str]) -> Optional[datetime]:
    if not valor:
        return None

    bruto = str(valor).strip()
    m = re.search(r"(\d{8})", bruto)

    if not m:
        return None

    try:
        return datetime.strptime(m.group(1), "%Y%m%d")
    except Exception:
        return None


def _ler_texto_ofx(caminho_arquivo: str) -> str:
    bruto_bytes = Path(caminho_arquivo).read_bytes()

    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return bruto_bytes.decode(enc)
        except Exception:
            continue

    return bruto_bytes.decode("latin-1", errors="ignore")


def _processar_ofx_manual(caminho_arquivo: str) -> Dict[str, Any]:
    try:
        texto = _ler_texto_ofx(caminho_arquivo)
        nome_arquivo = Path(caminho_arquivo).name

        bankid = _ofx_get_tag(texto, "BANKID") or _ofx_get_tag(texto, "BROKERID")
        banco, origem_banco = detectar_instituicao_com_origem(texto, nome_arquivo, bankid)

        conta = _ofx_get_tag(texto, "ACCTID") or _ofx_get_tag(texto, "ACCTKEY")

        dt_start = parse_data_ofx(_ofx_get_tag(texto, "DTSTART"))
        dt_end = parse_data_ofx(_ofx_get_tag(texto, "DTEND"))

        periodo = None
        origem_periodo = "nao_identificado"

        if dt_end:
            periodo = formatar_periodo(dt_end.month, dt_end.year)
            origem_periodo = "ofx_dtend"
        elif dt_start:
            periodo = formatar_periodo(dt_start.month, dt_start.year)
            origem_periodo = "ofx_dtstart"
        else:
            periodo, origem_periodo = extrair_periodo(
                texto=texto,
                nome_arquivo=nome_arquivo,
                caminho_arquivo=caminho_arquivo,
            )

        saldo_final = valor_para_float(_ofx_get_tag(texto, "BALAMT"))

        blocos = re.split(r"<STMTTRN>", texto, flags=re.IGNORECASE)[1:]
        movimentacoes: List[Dict[str, Any]] = []

        for bloco in blocos:
            bloco = re.split(r"</STMTTRN>|<STMTTRN>", bloco, flags=re.IGNORECASE)[0]

            dt = parse_data_ofx(_ofx_get_tag(bloco, "DTPOSTED") or _ofx_get_tag(bloco, "DTUSER"))
            valor = valor_para_float(_ofx_get_tag(bloco, "TRNAMT"))

            memo = (
                _ofx_get_tag(bloco, "MEMO")
                or _ofx_get_tag(bloco, "NAME")
                or _ofx_get_tag(bloco, "PAYEE")
                or "Transação"
            )

            fitid = _ofx_get_tag(bloco, "FITID")

            if dt is None or valor is None:
                continue

            movimentacoes.append({
                "data": dt.strftime("%d/%m/%Y"),
                "descricao": compactar_espacos(memo),
                "valor": abs(float(valor)),
                "natureza": "entrada" if valor >= 0 else "saida",
                "id_transacao": fitid,
                "origem": "ofx_manual",
            })

        banco_ok = banco and banco != "Desconhecido"
        periodo_ok = periodo and periodo != "Não identificado"

        status = "ok_completo" if banco_ok and periodo_ok else "revisar"

        mensagem = (
            "OFX lido com banco e período identificados."
            if status == "ok_completo"
            else "OFX lido, mas banco ou período precisam de revisão."
        )

        sem_movimento = len(movimentacoes) == 0

        confianca = calcular_confianca_metadados(
            banco=banco,
            periodo=periodo,
            tipo_documento="Extrato OFX",
            origem_banco=origem_banco,
            origem_periodo=origem_periodo,
            sem_movimento=sem_movimento,
        )

        resumo = {
            "modo_leitura": "ofx_estruturado",
            "metadados_extraidos": bool(banco_ok and periodo_ok),
            "sem_movimento": sem_movimento,
            "saldo_final": saldo_final,
            "conta": conta,
            "bankid": bankid,
            "qtd_movimentacoes": len(movimentacoes),
            "movimentacoes_flat": movimentacoes,
            "origem_extracao": "ofx_manual",
            "usou_ia": False,
            "observacao_usuario": None,
        }

        return montar_resultado(
            status_leitura=status,
            mensagem_leitura=mensagem,
            banco=banco,
            periodo=periodo,
            tipo_documento="Extrato OFX",
            confianca=confianca,
            origem_banco=origem_banco,
            origem_periodo=origem_periodo,
            resumo=resumo,
        )

    except Exception as e:
        return montar_resultado(
            status_leitura="nao_legivel",
            mensagem_leitura=f"Erro ao ler OFX: {e}",
            banco="Desconhecido",
            periodo=None,
            tipo_documento="Extrato OFX",
            confianca=0.0,
            origem_banco="erro",
            origem_periodo="erro",
            resumo={
                "modo_leitura": "ofx_erro",
                "metadados_extraidos": False,
                "sem_movimento": False,
                "saldo_final": None,
                "qtd_movimentacoes": 0,
                "movimentacoes_flat": [],
                "origem_extracao": "ofx_erro",
                "usou_ia": False,
                "observacao_usuario": None,
            },
        )


def _processar_ofx_ofxparse(caminho_arquivo: str) -> Optional[Dict[str, Any]]:
    if OfxParser is None:
        return None

    try:
        with open(caminho_arquivo, "rb") as fileobj:
            ofx = OfxParser.parse(fileobj)

        conta = getattr(ofx, "account", None)
        if conta is None:
            return None

        extrato = getattr(conta, "statement", None)
        if extrato is None:
            return None

        nome_arquivo = Path(caminho_arquivo).name
        routing_number = getattr(conta, "routing_number", None)

        banco, origem_banco = detectar_instituicao_com_origem(
            "",
            nome_arquivo,
            routing_number,
        )

        if banco == "Desconhecido" and routing_number:
            banco = f"Banco {routing_number}"
            origem_banco = "ofx_routing_number"

        start_date = getattr(extrato, "start_date", None)
        end_date = getattr(extrato, "end_date", None)

        periodo = None
        origem_periodo = "nao_identificado"

        if end_date:
            periodo = formatar_periodo(end_date.month, end_date.year)
            origem_periodo = "ofx_dtend"
        elif start_date:
            periodo = formatar_periodo(start_date.month, start_date.year)
            origem_periodo = "ofx_dtstart"
        else:
            periodo, origem_periodo = extrair_periodo(
                nome_arquivo=nome_arquivo,
                caminho_arquivo=caminho_arquivo,
            )

        movimentacoes = []

        for tx in getattr(extrato, "transactions", []) or []:
            valor = float(getattr(tx, "amount", 0) or 0)
            data_tx = getattr(tx, "date", None)

            if data_tx is None:
                continue

            movimentacoes.append({
                "data": data_tx.strftime("%d/%m/%Y"),
                "descricao": compactar_espacos(
                    getattr(tx, "memo", None)
                    or getattr(tx, "payee", None)
                    or "Transação"
                ),
                "valor": abs(valor),
                "natureza": "entrada" if valor >= 0 else "saida",
                "id_transacao": getattr(tx, "id", None),
                "origem": "ofxparse",
            })

        saldo = getattr(extrato, "balance", None)
        saldo_final = float(saldo) if saldo is not None else None

        banco_ok = banco and banco != "Desconhecido"
        periodo_ok = periodo and periodo != "Não identificado"
        status = "ok_completo" if banco_ok and periodo_ok else "revisar"

        mensagem = (
            "OFX lido com banco e período identificados."
            if status == "ok_completo"
            else "OFX lido, mas banco ou período precisam de revisão."
        )

        sem_movimento = len(movimentacoes) == 0

        confianca = calcular_confianca_metadados(
            banco=banco,
            periodo=periodo,
            tipo_documento="Extrato OFX",
            origem_banco=origem_banco,
            origem_periodo=origem_periodo,
            sem_movimento=sem_movimento,
        )

        resumo = {
            "modo_leitura": "ofx_estruturado",
            "metadados_extraidos": bool(banco_ok and periodo_ok),
            "sem_movimento": sem_movimento,
            "saldo_final": saldo_final,
            "conta": getattr(conta, "account_id", None) or getattr(conta, "number", None),
            "bankid": routing_number,
            "qtd_movimentacoes": len(movimentacoes),
            "movimentacoes_flat": movimentacoes,
            "origem_extracao": "ofxparse",
            "usou_ia": False,
            "observacao_usuario": None,
        }

        return montar_resultado(
            status_leitura=status,
            mensagem_leitura=mensagem,
            banco=banco,
            periodo=periodo,
            tipo_documento="Extrato OFX",
            confianca=confianca,
            origem_banco=origem_banco,
            origem_periodo=origem_periodo,
            resumo=resumo,
        )

    except Exception:
        return None


def processar_ofx(caminho_arquivo: str) -> Dict[str, Any]:
    resultado = _processar_ofx_ofxparse(caminho_arquivo)

    if resultado is not None:
        return resultado

    return _processar_ofx_manual(caminho_arquivo)


# ==========================================================
# PDF PRINCIPAL — SOMENTE METADADOS
# ==========================================================
def processar_pdf(caminho_arquivo: str, nome_arquivo: Optional[str] = None) -> Dict[str, Any]:
    nome_arquivo = nome_arquivo or Path(caminho_arquivo).name

    texto, origem_extracao = _extrair_texto_pdf_com_origem(caminho_arquivo)

    if not texto:
        return montar_resultado(
            status_leitura="nao_legivel",
            mensagem_leitura="PDF sem texto extraível ou ilegível.",
            banco="Desconhecido",
            periodo=None,
            tipo_documento="Desconhecido",
            confianca=0.0,
            origem_banco="nao_identificado",
            origem_periodo="nao_identificado",
            resumo={
                "modo_leitura": "pdf_metadados",
                "metadados_extraidos": False,
                "sem_movimento": False,
                "saldo_final": None,
                "qtd_movimentacoes": 0,
                "movimentacoes_flat": [],
                "origem_extracao": origem_extracao,
                "usou_ia": False,
                "observacao_usuario": None,
            },
        )

    banco, origem_banco = detectar_instituicao_com_origem(texto, nome_arquivo)

    periodo, origem_periodo = extrair_periodo(
        texto=texto,
        nome_arquivo=nome_arquivo,
        caminho_arquivo=caminho_arquivo,
    )

    tipo_documento = classificar_tipo_documento(texto, nome_arquivo, banco)
    sem_movimento = detectar_sem_movimento(texto)
    saldo_final = extrair_saldo_final_simples(texto)

    banco_ok = banco and banco != "Desconhecido"
    periodo_ok = periodo and periodo != "Não identificado"
    tipo_ok = tipo_documento and tipo_documento != "Desconhecido"

    metadados_extraidos = bool(banco_ok and periodo_ok)

    if metadados_extraidos:
        status = "ok_completo"
        mensagem = "Metadados essenciais extraídos. Conferência do conteúdo deve ser feita pelo usuário."
    else:
        status = "revisar"

        faltando = []
        if not banco_ok:
            faltando.append("banco")
        if not periodo_ok:
            faltando.append("período")

        mensagem = "Metadados incompletos. Revisar manualmente: " + ", ".join(faltando)

    confianca = calcular_confianca_metadados(
        banco=banco,
        periodo=periodo,
        tipo_documento=tipo_documento,
        origem_banco=origem_banco,
        origem_periodo=origem_periodo,
        sem_movimento=sem_movimento,
    )

    resumo = {
        "modo_leitura": "pdf_metadados",
        "metadados_extraidos": metadados_extraidos,
        "sem_movimento": bool(sem_movimento),
        "saldo_final": saldo_final,
        "qtd_movimentacoes": 0,
        "movimentacoes_flat": [],
        "movimentacoes_confiaveis": False,
        "origem_extracao": origem_extracao,
        "usou_ia": False,
        "observacao_usuario": None,
        "tipo_identificado": bool(tipo_ok),
    }

    return montar_resultado(
        status_leitura=status,
        mensagem_leitura=mensagem,
        banco=banco,
        periodo=periodo,
        tipo_documento=tipo_documento,
        confianca=confianca,
        origem_banco=origem_banco,
        origem_periodo=origem_periodo,
        resumo=resumo,
    )


# ==========================================================
# FUNIL PRINCIPAL
# ==========================================================
def processar_documento(caminho_arquivo: str, nome_arquivo: Optional[str] = None) -> Dict[str, Any]:
    nome_arquivo = nome_arquivo or Path(caminho_arquivo).name
    ext = Path(nome_arquivo).suffix.lower()

    if ext in EXTENSOES_OFX:
        return processar_ofx(caminho_arquivo)

    if ext in EXTENSOES_PDF:
        return processar_pdf(caminho_arquivo, nome_arquivo)

    return montar_resultado(
        status_leitura="nao_legivel",
        mensagem_leitura=f"Extensão não suportada: {ext}",
        banco="Desconhecido",
        periodo=None,
        tipo_documento="Desconhecido",
        confianca=0.0,
        origem_banco="nao_identificado",
        origem_periodo="nao_identificado",
        resumo={
            "modo_leitura": "extensao_nao_suportada",
            "metadados_extraidos": False,
            "sem_movimento": False,
            "saldo_final": None,
            "qtd_movimentacoes": 0,
            "movimentacoes_flat": [],
            "origem_extracao": "extensao_nao_suportada",
            "usou_ia": False,
            "observacao_usuario": None,
        },
    )


# ==========================================================
# MONGO / LOTE
# ==========================================================
def _status_para_banco(status_leitura: str) -> str:
    """
    Nova regra:
    - ok_completo = processado
    - ok_metadados = processado
    - revisar = processado_com_alerta
    - nao_legivel/erro = nao_legivel
    """
    if status_leitura in {"ok_completo", "ok_metadados", "ok"}:
        return "processado"

    if status_leitura in {"revisar", "processado_com_alerta"}:
        return "processado_com_alerta"

    return "nao_legivel"


def processar_lote_documentos() -> None:
    if arquivos_col is None:
        print("[x] Mongo não configurado. Use o teste.py para rodar localmente.")
        return

    pendentes = list(arquivos_col.find({"status": "pendente"}))

    if not pendentes:
        print("\n[✓] Nenhum documento pendente.")
        return

    print(f"\n=== Processando {len(pendentes)} documento(s) ===\n")

    for arq in pendentes:
        caminho = arq.get("caminho_completo", "")
        nome = arq.get("nome_arquivo", Path(caminho).name if caminho else "Desconhecido")
        _id = arq.get("_id")

        print(f"Lendo: {nome}...")

        if not caminho or not os.path.exists(caminho):
            arquivos_col.update_one(
                {"_id": _id},
                {"$set": {
                    "status": "nao_legivel",
                    "status_leitura": "nao_legivel",
                    "mensagem_leitura": "Arquivo não encontrado.",
                    "data_processamento": datetime.now(),
                }},
            )
            continue

        dados = processar_documento(caminho, nome)
        status_leitura = dados.get("status_leitura", "nao_legivel")
        db_status = _status_para_banco(status_leitura)

        arquivos_col.update_one(
            {"_id": _id},
            {"$set": {
                "tipo_documento": dados.get("tipo_documento", "Desconhecido"),
                "banco": dados.get("banco", "Desconhecido"),
                "periodo": dados.get("periodo", "N/A"),
                "status": db_status,
                "status_leitura": status_leitura,
                "mensagem_leitura": dados.get("mensagem_leitura"),
                "confianca_leitura": dados.get("confianca"),
                "origem_banco": dados.get("origem_banco"),
                "origem_periodo": dados.get("origem_periodo"),
                "conteudo": json.dumps(
                    dados.get("resumo_estruturado", {}),
                    ensure_ascii=False,
                    default=_json_default,
                ),
                "data_processamento": datetime.now(),
            }},
        )

        print(
            f"  [✓] Status: {db_status} | "
            f"{dados.get('banco')} | "
            f"{dados.get('periodo')} | "
            f"{dados.get('tipo_documento')}"
        )


# ==========================================================
# CLI
# ==========================================================
def main() -> None:
    # Uso:
    # python workers/leitor_ia.py caminho/arquivo.pdf
    if len(sys.argv) > 1:
        for caminho in sys.argv[1:]:
            resultado = processar_documento(caminho, Path(caminho).name)
            print(json.dumps(resultado, indent=4, ensure_ascii=False, default=_json_default))
        return

    processar_lote_documentos()


if __name__ == "__main__":
    main()