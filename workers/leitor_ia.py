from __future__ import annotations
import os
import sys
import io
import re
import json
import unicodedata
from collections import Counter
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

# Configuração opcional do Tesseract
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
# CONFIGURAÇÕES
# ==========================================================
USAR_OCR = os.getenv("LEITOR_IA_USAR_OCR", "1").strip().lower() not in {"0", "false", "nao", "não"}
USAR_IA = os.getenv("LEITOR_IA_USAR_IA", "0").strip().lower() in {"1", "true", "sim", "s"}
MODELO_IA = os.getenv("LEITOR_IA_MODELO", "gpt-4o-mini")
CONFIAR_MOVIMENTACOES_INVESTIMENTOS = os.getenv(
    "LEITOR_IA_CONFIAR_INVESTIMENTOS", "0"
).strip().lower() in {"1", "true", "sim", "s"}

EXTENSOES_OFX = (".ofx", ".ofc", ".qfx")
EXTENSOES_PDF = (".pdf",)

# Dinheiro em formato brasileiro, com sinal opcional e R$ opcional.
MONEY_PATTERN = (
    r"(?<!\d)(?:[+-]\s*)?(?:R\$\s*)?\d{1,3}(?:\.\d{3})*,\d{2}(?!\d)"
    r"|(?<!\d)(?:[+-]\s*)?(?:R\$\s*)?\d+,\d{2}(?!\d)"
)
RE_MONEY = re.compile(MONEY_PATTERN, re.IGNORECASE)
RE_DATA_COMPLETA = re.compile(r"\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,4})\b")
RE_DATA_CURTA = re.compile(r"\b(\d{1,2})\s*/\s*(\d{1,2})(?!\s*/\s*\d)\b")
RE_DATA_INICIO_LINHA = re.compile(
    r"^\s*(\d{1,2}\s*/\s*\d{1,2}(?:\s*/\s*\d{2,4})?)\b"
)

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
    "1": "Banco do Brasil",
    "001": "Banco do Brasil",
    "0001": "Banco do Brasil",
    "237": "Bradesco",
    "033": "Santander",
    "33": "Santander",
    "341": "Itaú",
    "0341": "Itaú",
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
        "corretora de cambio",
        "corretora de câmbio",
        "cdb banco xp",
    ]),
    ("Omie.CASH", [
        "omie.cash",
        "omie cash",
        "extrato de omie",
        "conta omie",
    ]),
    ("Transpocred", [
        "transpocred",
        "sistema ailos",
    ]),
    ("Banco do Brasil", [
        "banco do brasil",
        "bb ",
        " bb",
        "extrato de conta corrente",
        "consultas - extrato de conta corrente",
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
        "invest_facil",
        "invest-facil",
        "invest fácil",
        "alo bradesco",
        "alô bradesco",
        "valor resgate liquido",
        "valor resgate líquido",
    ]),
    ("Santander", ["santander"]),
    ("Sicredi", ["sicredi"]),
    ("Sicoob", ["sicoob"]),
    ("C6 Bank", ["c6 bank", "banco c6"]),
]

TERMOS_RODAPE_OU_MENU = [
    "atendimento ao cliente",
    "ouvidoria",
    "servico de atendimento",
    "serviço de atendimento",
    "sac -",
    "sac ",
    "mapa do site",
    "ajudas e tutoriais",
    "fale conosco",
    "voltar ao topo",
    "extrato simples para conferencia",
    "extrato simples para conferência",
    "informacoes confidencias",
    "informações confidenciais",
    "estas informacoes sao confidencias",
    "estas informações são confidenciais",
    "sujeito a atualizacoes",
    "sujeito a atualizações",
    "para acesso ao sac",
    "dias uteis",
    "dias úteis",
    "https://",
    "http://",
]

FRASES_SEM_MOVIMENTO = [
    "nao houve movimentacoes",
    "nao houve movimentacoes na conta durante o periodo informado",
    "nao houve movimentacao",
    "sem movimentacoes",
    "sem movimentacao",
    "sem lancamentos",
    "nao ha lancamentos",
    "nao há lançamentos",
    "nenhuma movimentacao",
    "nenhuma movimentação",
    "total de entradas 0,00",
    "total de saidas 0,00",
]

# ==========================================================
# HELPERS GERAIS
# ==========================================================
def normalizar_texto(texto: str) -> str:
    """Normaliza acentos, caixa e espaços para facilitar regex."""
    if not texto:
        return ""

    texto = str(texto).replace("\xa0", " ").replace("\ufeff", " ")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.lower()
    texto = re.sub(r"[\t\r\f\v]+", " ", texto)
    texto = re.sub(r" {2,}", " ", texto)
    return texto.strip()


def compactar_espacos(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r"\s+", " ", str(texto)).strip()


def somente_digitos(texto: Any) -> str:
    return re.sub(r"\D+", "", str(texto or ""))


def valor_para_float(valor: Any, preservar_sinal: bool = True) -> Optional[float]:
    """
    Converte valores brasileiros/OFX para float.

    Exemplos:
    - "R$ 1.234,56" -> 1234.56
    - "-R$ 1.234,56" -> -1234.56
    - "1234.56" -> 1234.56
    """
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

    sinal = -1 if "-" in texto_original and preservar_sinal else 1

    texto = texto_original.upper()
    texto = texto.replace("R$", "")
    texto = texto.replace("+", "")
    texto = texto.replace("-", "")
    texto = texto.strip()
    texto = re.sub(r"[^\d,\.]", "", texto)

    if not texto:
        return None

    try:
        # Formato brasileiro: 1.234,56
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        # Formato OFX/americano: 1234.56
        return sinal * float(texto)
    except Exception:
        return None


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


def periodo_para_mes_ano(periodo: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not periodo:
        return None, None
    m = re.search(r"^(\d{2})/(\d{4})$", periodo.strip())
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def normalizar_data_br(data: str, periodo: Optional[str] = None) -> Optional[str]:
    """Normaliza data dd/mm ou dd/mm/aaaa para dd/mm/aaaa."""
    if not data:
        return None

    data = re.sub(r"\s+", "", data)
    partes = data.split("/")

    try:
        if len(partes) == 2:
            dia = int(partes[0])
            mes = int(partes[1])
            _, ano_periodo = periodo_para_mes_ano(periodo)
            ano = ano_periodo or datetime.now().year
        elif len(partes) == 3:
            dia = int(partes[0])
            mes = int(partes[1])
            ano = int(partes[2])
            if ano < 100:
                ano += 2000
        else:
            return None

        datetime(ano, mes, dia)
        return f"{dia:02d}/{mes:02d}/{ano:04d}"
    except Exception:
        return None


def parse_data_ofx(valor: Optional[str]) -> Optional[datetime]:
    if not valor:
        return None

    bruto = str(valor).strip()
    # OFX costuma vir como YYYYMMDDHHMMSS[-3:BRT]
    m = re.search(r"(\d{8})", bruto)
    if not m:
        return None

    try:
        return datetime.strptime(m.group(1), "%Y%m%d")
    except Exception:
        return None


def data_em_periodo(data_br: Optional[str], periodo: Optional[str]) -> bool:
    if not data_br or not periodo:
        return True

    m_periodo, a_periodo = periodo_para_mes_ano(periodo)
    m_data = re.search(r"\d{2}/(\d{2})/(\d{4})", data_br)

    if not m_periodo or not a_periodo or not m_data:
        return True

    return int(m_data.group(1)) == m_periodo and int(m_data.group(2)) == a_periodo

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

            # Binarização ajuda em PDF escaneado.
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
    """Função pública compatível com seu teste.py antigo."""
    texto, _origem = _extrair_texto_pdf_com_origem(caminho_pdf)
    return texto

# ==========================================================
# BANCO / TIPO / PERÍODO
# ==========================================================
def _detectar_instituicao_com_origem(
    texto: str,
    nome_arquivo: str = "",
    bank_id: Optional[str] = None,
) -> Tuple[str, str]:
    if bank_id:
        banco_por_id = BANKID_PARA_BANCO.get(str(bank_id).lstrip("0")) or BANKID_PARA_BANCO.get(str(bank_id))
        if banco_por_id:
            return banco_por_id, "bankid"

    nome_norm = normalizar_texto(nome_arquivo)
    texto_norm = normalizar_texto(texto)

    # Prioriza nome do arquivo quando ele é explícito.
    for nome, termos in INSTITUICOES:
        if any(termo in nome_norm for termo in termos):
            return nome, "nome_arquivo"

    combinado = f"{texto_norm} {nome_norm}"
    for nome, termos in INSTITUICOES:
        if any(termo in combinado for termo in termos):
            return nome, "texto"

    return "Desconhecido", "nao_identificado"


def detectar_instituicao(texto: str, nome_arquivo: str = "") -> str:
    """Função pública compatível com versões anteriores."""
    banco, _origem = _detectar_instituicao_com_origem(texto, nome_arquivo)
    return banco


def classificar_tipo_documento(texto: str, nome_arquivo: str = "", banco: str = "") -> str:
    """
    Classificação com prioridade para documentos especiais.

    Ordem:
    1. Borderô / Relatório Financeiro
    2. Relatório de Conciliação
    3. Extrato de Cotas/Capital
    4. Extrato de Investimentos
    5. Extrato Bancário
    """
    t = normalizar_texto(f"{nome_arquivo}\n{texto}")
    banco_norm = normalizar_texto(banco)

    # 1) Borderô / relatório financeiro
    if any(x in t for x in [
        "bordero",
        "borderô",
        "bordero para pagamentos",
        "borderô para pagamentos",
        "bordero para pagamentos e recebimentos",
        "borderô para pagamentos e recebimentos",
        "relacao de creditos",
        "relação de créditos",
        "relacao do debito",
        "relação do débito",
        "pagamentos e recebimentos diarios",
        "pagamentos e recebimentos diários",
        "fornecedor nº titulo vencimento valor",
        "fornecedor n titulo vencimento valor",
        "saldos bancos saldo inicial entradas no dia",
    ]):
        return "Borderô / Relatório Financeiro"

    # 2) Relatório de conciliação
    if any(x in t for x in [
        "conciliacao",
        "conciliação",
        "extrato sicredi rbm",
        "todas categorias",
        "cliente/fornecedor historico categoria entrada saida",
        "cliente/fornecedor histórico categoria entrada saída",
        "historico categoria entrada saida saldo do dia",
        "histórico categoria entrada saída saldo do dia",
        "diferenca entrada saida",
        "diferença entrada saída",
        "saldo do dia (s)",
    ]):
        return "Relatório de Conciliação"

    # 3) Cotas / capital
    if any(x in t for x in [
        "extrato do capital",
        "extrato de capital",
        "cotas capitais",
        "cotas capital",
        "cr. cotas",
        "demonstrativo de capital",
        "movimentacao de capital social",
        "movimentação de capital social",
    ]):
        return "Extrato de Cotas/Capital"

    # 4) Investimentos
    if any(x in t for x in [
        "xp investimentos corretora",
        "cdb banco xp",
        "resgate cdb",
        "compra cdb",
        "aplicacao compromissada",
        "aplicação compromissada",
        "recompra compromissada",
        "fundos/clubes",
        "termos a vencer",
        "termos à vencer",

        # Bradesco Invest Fácil / CDB
        "invest facil",
        "invest_facil",
        "invest-facil",
        "invest fácil",
        "investimentos bradesco",
        "valor resgate liquido",
        "valor resgate líquido",
        "valor resgate bruto",
        "valor renda bruta",
        "operacao: a - aplicacao r - resgate",
        "operação: a - aplicação r - resgate",
        "total de aplicacoes",
        "total de aplicações",
        "total de resgates",
    ]):
        return "Extrato de Investimentos"

    if banco_norm == "xp investimentos":
        return "Extrato de Investimentos"

    # 5) Conta corrente / extrato bancário
    if any(x in t for x in [
        "conta corrente / consulta",
        "consulta - extrato de conta corrente",
        "consultas - extrato de conta corrente",
        "extrato de conta corrente",
        "/conta-corrente/consultas/extrato",
        "conta corrente",
        "lancamentos do periodo",
        "lançamentos do período",
        "data lancamentos razao social",
        "data lançamentos razão social",
    ]):
        return "Extrato Bancário"

    if "extrato" in t:
        return "Extrato Bancário"

    return "Desconhecido"


def tipo_documento_nao_deve_confiar_movimentacoes(tipo_documento: str) -> bool:
    """
    Documentos que podem ter banco/período corretos, mas movimentações não devem
    ser marcadas como confiáveis pelo parser genérico.
    """
    tipo_norm = normalizar_texto(tipo_documento)

    return any(x in tipo_norm for x in [
        "investimento",
        "bordero",
        "borderô",
        "relatorio financeiro",
        "relatório financeiro",
        "conciliacao",
        "conciliação",
    ])


def extrair_periodo_nome_arquivo(nome_arquivo: str) -> Optional[str]:
    if not nome_arquivo:
        return None

    nome_original = str(nome_arquivo)
    nome = normalizar_texto(nome_original)

    # 04.2026, 04-2026, 04_2026, 04/2026
    m = re.search(r"(?<!\d)(0?[1-9]|1[0-2])\s*[\.\-_\/]\s*(20\d{2}|19\d{2})(?!\d)", nome)
    if m:
        return formatar_periodo(m.group(1), m.group(2))

    # 2026-04, 2026_04
    m = re.search(r"(?<!\d)(20\d{2}|19\d{2})\s*[\.\-_\/]\s*(0?[1-9]|1[0-2])(?!\d)", nome)
    if m:
        return formatar_periodo(m.group(2), m.group(1))

    # ABRIL 2026 / ABRIL_2026 / ABRIL-2026
    # Usa borda alfabética em vez de \b porque underscore é considerado caractere de palavra.
    for mes_nome, mes_num in MESES.items():
        mes_norm = re.escape(normalizar_texto(mes_nome))
        padrao = rf"(?<![a-z]){mes_norm}(?![a-z])[^0-9a-z]*(20\d{{2}}|19\d{{2}})"
        m = re.search(padrao, nome)
        if m:
            return formatar_periodo(mes_num, m.group(1))

    return None


def _extrair_periodo_texto_com_origem(texto: str) -> Tuple[Optional[str], str]:
    if not texto:
        return None, "nao_identificado"

    t = normalizar_texto(texto)

    # Intervalos com data inicial e final. Para competência, prioriza a data final.
    padroes_intervalo = [
        r"periodo\s+do\s+extrato\s+de\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})\s+(?:ate|a)\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})",
        r"periodo\s+de\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})\s+(?:ate|a)\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})",
        r"extrato\s+de\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})\s+(?:ate|a)\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})",
        r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})\s+(?:ate|a)\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})",
    ]

    for padrao in padroes_intervalo:
        m = re.search(padrao, t, re.IGNORECASE)
        if m:
            mes_final = m.group(5)
            ano_final = m.group(6)
            periodo = formatar_periodo(mes_final, ano_final)
            if periodo:
                return periodo, "texto_intervalo_final"

    # Exemplo: "Mês: Abril/2026", "Abril/2026".
    # Atenção: em extratos de investimento aparecem vencimentos como SET/2026 dentro
    # de descrições de CDB. Por isso, abreviações só valem com contexto explícito.
    for mes_nome, mes_num in MESES.items():
        mes_nome_norm = normalizar_texto(mes_nome)
        eh_abreviado = len(mes_nome_norm) <= 3

        if eh_abreviado:
            padroes_mes = [
                rf"\b(?:mes|competencia|periodo)\s*[:\-]?\s*{re.escape(mes_nome_norm)}\s*/\s*(20\d{{2}}|19\d{{2}})\b",
                rf"\b(?:mes|competencia|periodo)\s*[:\-]?\s*{re.escape(mes_nome_norm)}\s+de\s+(20\d{{2}}|19\d{{2}})\b",
            ]
        else:
            padroes_mes = [
                rf"(?<![a-z]){re.escape(mes_nome_norm)}(?![a-z])\s*/\s*(20\d{{2}}|19\d{{2}})\b",
                rf"(?<![a-z]){re.escape(mes_nome_norm)}(?![a-z])\s+de\s+(20\d{{2}}|19\d{{2}})\b",
                rf"\b(?:mes|competencia|periodo)\s*[:\-]?\s*{re.escape(mes_nome_norm)}\s*/\s*(20\d{{2}}|19\d{{2}})\b",
            ]

        for padrao in padroes_mes:
            m = re.search(padrao, t, re.IGNORECASE)
            if m:
                periodo = formatar_periodo(mes_num, m.group(1))
                if periodo:
                    return periodo, "texto_mes_extenso"

    # Exemplo: Período: 04/2026
    m = re.search(r"\b(?:competencia|competência|periodo|período|mes|mês)\s*[:\-]?\s*(0?[1-9]|1[0-2])\s*/\s*(20\d{2}|19\d{2})\b", t)
    if m:
        periodo = formatar_periodo(m.group(1), m.group(2))
        if periodo:
            return periodo, "texto_mes_ano"

    return None, "nao_identificado"


def extrair_periodo_por_datas_movimentacoes(texto: str) -> Optional[str]:
    if not texto:
        return None

    datas = RE_DATA_COMPLETA.findall(texto)
    contador: Counter[Tuple[str, str]] = Counter()

    for dia, mes, ano in datas:
        try:
            data = datetime(int(ano if len(ano) == 4 else f"20{ano}"), int(mes), int(dia))
            # Evita usar datas muito isoladas de consulta/emissão quando possível.
            contador[(f"{data.month:02d}", f"{data.year:04d}")] += 1
        except Exception:
            continue

    if not contador:
        return None

    (mes, ano), qtd = contador.most_common(1)[0]
    if qtd >= 2:
        return formatar_periodo(mes, ano)

    return None


def extrair_periodo(texto: str) -> str:
    """Função pública compatível com versões anteriores."""
    periodo, _origem = _extrair_periodo_texto_com_origem(texto)
    return periodo or "Não identificado"

# ==========================================================
# SEM MOVIMENTO / SALDO
# ==========================================================
def linha_descartavel(linha: str) -> bool:
    if not linha:
        return True

    norm = normalizar_texto(linha)

    if len(norm) <= 1:
        return True

    if any(t in norm for t in TERMOS_RODAPE_OU_MENU):
        return True

    # Menus comuns de internet banking.
    if norm in {"veja tambem", "veja também", "lancamentos futuros", "lançamentos futuros"}:
        return True

    termos_cabecalho_resumo = [
        "data cliente/fornecedor",
        "cliente/fornecedor historico",
        "cliente/fornecedor histórico",
        "historico categoria entrada saida",
        "histórico categoria entrada saída",
        "entrada saida saldo do dia",
        "entrada saída saldo do dia",
        "saldo do dia (s)",
        "totais",
        "totalizador",
        "diferenca entrada saida",
        "diferença entrada saída",
        "saldo anterior",
        "saldo final",
        "saldo inicial",
        "saldo total",
    ]

    if any(t in norm for t in termos_cabecalho_resumo):
        return True

    return False


def detectar_sem_movimento(texto: str, movimentacoes: Optional[List[Dict[str, Any]]] = None) -> bool:
    """
    Detecta ausência de movimento.

    Regra importante:
    se já existem movimentações extraídas, não marca sem movimento. Isso evita erro em
    extratos que trazem frases como "A conta não foi movimentada", mas ainda exibem
    tarifas/saldos/lançamentos contábeis.
    """
    if movimentacoes:
        return False

    t = normalizar_texto(texto)

    if any(frase in t for frase in [normalizar_texto(x) for x in FRASES_SEM_MOVIMENTO]):
        return True

    # Omie e similares: totais zerados.
    tem_entrada_zero = re.search(r"total\s+de\s+entradas\s+0,00", t) is not None
    tem_saida_zero = re.search(r"total\s+de\s+saidas\s+0,00", t) is not None
    if tem_entrada_zero and tem_saida_zero:
        return True

    return False


def extrair_saldo_final(texto: str) -> Optional[float]:
    if not texto:
        return None

    t = normalizar_texto(texto)

    padroes = [
        r"saldo\s+final\s+do\s+periodo(?:\s*\([^)]*\))?\s*[:\-]?\s*(?:r\$\s*)?([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
        r"saldo\s+final\s*[:\-]?\s*(?:r\$\s*)?([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
        r"saldo\s+disponivel\s*[:\-]?\s*(?:r\$\s*)?([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
        r"saldo\s+total\s*(?:\(r\$\))?\s*[:\-]?\s*(?:r\$\s*)?([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
        r"s\s*a\s*l\s*d\s*o\s*(?:r\$)?\s*([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
    ]

    for padrao in padroes:
        m = re.search(padrao, t, re.IGNORECASE)
        if m:
            return valor_para_float(m.group(1), preservar_sinal=True)

    # Itaú: último SDO CTA/APL AUTOMATICAS costuma representar saldo final da listagem.
    saldos_sdo = re.findall(
        r"sdo\s+cta/apl\s+automaticas\s+([+-]?\d{1,3}(?:\.\d{3})*,\d{2}|[+-]?\d+,\d{2})",
        t,
        flags=re.IGNORECASE,
    )
    if saldos_sdo:
        return valor_para_float(saldos_sdo[-1], preservar_sinal=True)

    return None

# ==========================================================
# EXTRAÇÃO DE MOVIMENTAÇÕES PDF
# ==========================================================
def _limpar_descricao_transacao(descricao: str) -> str:
    if not descricao:
        return "Transação"

    desc = descricao
    desc = re.sub(RE_DATA_COMPLETA, " ", desc)
    desc = re.sub(RE_DATA_CURTA, " ", desc)
    desc = RE_MONEY.sub(" ", desc)
    desc = re.sub(r"\b(?:R\$|C|D)\b", " ", desc, flags=re.IGNORECASE)
    desc = re.sub(r"\s{2,}", " ", desc)
    desc = desc.strip(" -|:;.,")

    return desc or "Transação"


def _inferir_natureza(linha: str, valor_token: str, valor_float: Optional[float]) -> str:
    token_norm = normalizar_texto(valor_token)

    if "-" in valor_token or (valor_float is not None and valor_float < 0):
        return "saida"

    # Procura D/C logo após o token.
    try:
        idx = linha.find(valor_token)
        depois = linha[idx + len(valor_token): idx + len(valor_token) + 8]
        antes = linha[max(0, idx - 8): idx]
        entorno = normalizar_texto(f"{antes} {depois}")

        if re.search(r"\bd\b", entorno):
            return "saida"
        if re.search(r"\bc\b", entorno):
            return "entrada"
    except Exception:
        pass

    # Sem sinal e sem C/D, valor positivo é tratado como entrada.
    # Não usamos palavras como "compra" aqui porque "recompra" em investimentos
    # costuma ser crédito/resgate e quebrava a natureza das transações da XP.
    return "entrada"


def _primeiro_valor_transacao(linha: str) -> Tuple[Optional[str], Optional[float], Optional[str]]:
    """
    Retorna token, valor absoluto e natureza.

    Quando há valor e saldo na mesma linha, geralmente o primeiro valor monetário é o valor
    da movimentação e o último é o saldo.
    """
    matches = list(RE_MONEY.finditer(linha))
    if not matches:
        return None, None, None

    # Evita tratar linhas óbvias de saldo como movimentação.
    norm = normalizar_texto(linha)
    if any(x in norm for x in [
        "saldo anterior",
        "saldo inicial",
        "saldo final",
        "saldo disponivel",
        "saldo disponível",
        "saldo total projetado",
        "sdo cta/apl automaticas",
    ]):
        return None, None, None

    match = matches[0]
    token = match.group(0)
    valor = valor_para_float(token, preservar_sinal=True)

    if valor is None:
        return None, None, None

    natureza = _inferir_natureza(linha, token, valor)
    return token, abs(valor), natureza


def extrair_movimentacoes_genericas(texto: str, periodo: Optional[str] = None, tipo_documento: str = "") -> List[Dict[str, Any]]:
    """
    Parser genérico por linhas.

    Ele não tenta conhecer cada banco. Só procura padrões comuns:
    - linha iniciando com data dd/mm ou dd/mm/aaaa;
    - valor monetário na própria linha ou nas próximas linhas;
    - sinal negativo ou C/D para natureza.
    """
    if not texto:
        return []

    linhas = [compactar_espacos(l) for l in texto.splitlines() if compactar_espacos(l)]
    movimentacoes: List[Dict[str, Any]] = []

    buffer_data: Optional[str] = None
    buffer_desc: List[str] = []
    linhas_apos_data = 0

    def flush_com_valor(linha_valor: str) -> bool:
        nonlocal buffer_data, buffer_desc, linhas_apos_data

        if not buffer_data:
            return False

        token, valor, natureza = _primeiro_valor_transacao(linha_valor)
        if valor is None or natureza is None:
            return False

        descricao = _limpar_descricao_transacao(" ".join(buffer_desc))

        movimentacoes.append({
            "data": buffer_data,
            "descricao": descricao,
            "valor": valor,
            "natureza": natureza,
            "origem": "pdf_regex",
            "_linha_origem": compactar_espacos(linha_valor),

        })

        buffer_data = None
        buffer_desc = []
        linhas_apos_data = 0
        return True

    for linha in linhas:
        if linha_descartavel(linha):
            continue

        linha_norm = normalizar_texto(linha)

        # Ignora cabeçalhos comuns.
        if any(x in linha_norm for x in [
            "data lancamento",
            "data lançamento",
            "dt. balancete",
            "dt. movimento",
            "historico valor saldo",
            "histórico valor saldo",
            "liq mov historico valor saldo",
            "liq mov histórico valor saldo",
        ]):
            continue

        match_data_inicio = RE_DATA_INICIO_LINHA.search(linha)

        if match_data_inicio:
            # Se havia uma transação anterior sem valor, descarta para não grudar com próxima.
            buffer_data = None
            buffer_desc = []
            linhas_apos_data = 0

            data_br = normalizar_data_br(match_data_inicio.group(1), periodo)
            if not data_br:
                continue

            resto = linha[match_data_inicio.end():].strip()

            # XP e similares podem ter duas datas no começo: Liq e Mov.
            match_segunda_data = RE_DATA_INICIO_LINHA.search(resto)
            if match_segunda_data:
                data2 = normalizar_data_br(match_segunda_data.group(1), periodo)
                if data2:
                    data_br = data2
                    resto = resto[match_segunda_data.end():].strip()

            # Remove linhas de consulta/emissão que começam com data + hora + nome do banco.
            if re.search(r"^\s*\d{1,2}:\d{2}\b", resto) and any(
                banco in linha_norm for banco in ["xp investimentos", "transpocred", "itau", "itaú"]
            ):
                continue

            # Ignora linhas óbvias de saldo.
            if any(x in linha_norm for x in ["saldo anterior", "saldo inicial", "saldo final", "saldo total"]):
                continue
            if re.search(r"s\s*a\s*l\s*d\s*o", linha_norm):
                continue

            buffer_data = data_br
            buffer_desc = [resto] if resto else []
            linhas_apos_data = 0

            if RE_MONEY.search(linha):
                flush_com_valor(linha)

            continue

        # Continuação de transação iniciada em linha anterior.
        if buffer_data:
            linhas_apos_data += 1

            # Limite para evitar grudar rodapé inteiro em uma transação.
            if linhas_apos_data > 4:
                buffer_data = None
                buffer_desc = []
                linhas_apos_data = 0
                continue

            if RE_MONEY.search(linha):
                # Antes de salvar, adiciona a linha se ela tiver texto descritivo relevante.
                sem_valor = RE_MONEY.sub(" ", linha)
                if compactar_espacos(sem_valor):
                    buffer_desc.append(sem_valor)
                flush_com_valor(linha)
            else:
                buffer_desc.append(linha)

    # Deduplicação simples.
    unicas: List[Dict[str, Any]] = []
    vistos = set()
    for mov in movimentacoes:
        chave = (
            mov.get("data"),
            normalizar_texto(mov.get("descricao", ""))[:80],
            round(float(mov.get("valor") or 0), 2),
            mov.get("natureza"),
            normalizar_texto(mov.get("_linha_origem", "")),
        )

        if chave in vistos:
            continue

        vistos.add(chave)
        mov.pop("_linha_origem", None)
        unicas.append(mov)

    return unicas


def movimentacoes_sao_confiaveis(
    movimentacoes: List[Dict[str, Any]],
    texto: str = "",
    periodo: Optional[str] = None,
    tipo_documento: str = "",
) -> bool:
    if not movimentacoes:
        return False

    tipo_norm = normalizar_texto(tipo_documento)

    if tipo_documento_nao_deve_confiar_movimentacoes(tipo_documento):
        return False

    if "investimento" in tipo_norm and not CONFIAR_MOVIMENTACOES_INVESTIMENTOS:
        return False

    ruins = 0

    termos_ruins = [normalizar_texto(t) for t in TERMOS_RODAPE_OU_MENU] + [
        "data da consulta",
        "codigo assessor",
        "código assessor",
        "informacoes detalhadas do saldo",
        "informações detalhadas do saldo",
        "lancamentos futuros",
        "lançamentos futuros",
    ]

    for mov in movimentacoes:
        descricao = normalizar_texto(mov.get("descricao", ""))
        valor = mov.get("valor")
        data = mov.get("data")

        try:
            valor_float = float(valor)
        except Exception:
            valor_float = 0.0

        if valor_float <= 0:
            ruins += 1
            continue

        if len(descricao) > 220:
            ruins += 1
            continue

        if any(termo in descricao for termo in termos_ruins):
            ruins += 1
            continue

        if periodo and not data_em_periodo(data, periodo):
            ruins += 1
            continue

    percentual_ruim = ruins / len(movimentacoes)

    return percentual_ruim <= 0.25


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


def _detectar_banco_ofx_manual(texto: str, nome_arquivo: str = "") -> Tuple[str, str, Optional[str]]:
    bankid = _ofx_get_tag(texto, "BANKID") or _ofx_get_tag(texto, "BROKERID")
    banco, origem = _detectar_instituicao_com_origem(texto, nome_arquivo, bankid)
    return banco, origem, bankid


def _processar_ofx_manual(caminho_arquivo: str) -> Dict[str, Any]:
    try:
        bruto_bytes = Path(caminho_arquivo).read_bytes()

        # OFX antigo pode vir em latin-1/cp1252.
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                texto = bruto_bytes.decode(enc)
                break
            except Exception:
                texto = ""
        if not texto:
            texto = bruto_bytes.decode("latin-1", errors="ignore")

        nome_arquivo = Path(caminho_arquivo).name
        banco, origem_banco, bankid = _detectar_banco_ofx_manual(texto, nome_arquivo)

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
            periodo = extrair_periodo_nome_arquivo(nome_arquivo)
            origem_periodo = "nome_arquivo" if periodo else "nao_identificado"

        saldo_final = valor_para_float(_ofx_get_tag(texto, "BALAMT"), preservar_sinal=True)

        blocos = re.split(r"<STMTTRN>", texto, flags=re.IGNORECASE)[1:]
        movimentacoes: List[Dict[str, Any]] = []

        for bloco in blocos:
            # Corta no próximo bloco/fechamento, se houver.
            bloco = re.split(r"</STMTTRN>|<STMTTRN>", bloco, flags=re.IGNORECASE)[0]

            dt = parse_data_ofx(_ofx_get_tag(bloco, "DTPOSTED") or _ofx_get_tag(bloco, "DTUSER"))
            valor = valor_para_float(_ofx_get_tag(bloco, "TRNAMT"), preservar_sinal=True)
            memo = _ofx_get_tag(bloco, "MEMO") or _ofx_get_tag(bloco, "NAME") or _ofx_get_tag(bloco, "PAYEE") or "Transação"
            trntype = (_ofx_get_tag(bloco, "TRNTYPE") or "").upper()
            fitid = _ofx_get_tag(bloco, "FITID")

            if dt is None or valor is None:
                continue

            natureza = "entrada" if valor >= 0 else "saida"
            if trntype in {"DEBIT", "PAYMENT", "FEE", "SRVCHG", "CHECK", "ATM", "POS", "XFER"} and valor < 0:
                natureza = "saida"
            elif trntype in {"CREDIT", "DEP", "DIRECTDEP", "INT", "DIV"} and valor >= 0:
                natureza = "entrada"

            movimentacoes.append({
                "data": dt.strftime("%d/%m/%Y"),
                "descricao": compactar_espacos(memo),
                "valor": abs(float(valor)),
                "natureza": natureza,
                "id_transacao": fitid,
                "origem": "ofx_manual",
            })

        status = "ok_completo" if banco != "Desconhecido" and periodo else "nao_legivel"
        mensagem = "Lido via OFX." if status == "ok_completo" else "OFX lido, mas banco ou período não foram identificados."

        resumo = {
            "sem_movimento": len(movimentacoes) == 0,
            "saldo_final": saldo_final,
            "conta": conta,
            "bankid": bankid,
            "qtd_movimentacoes": len(movimentacoes),
            "movimentacoes_flat": movimentacoes,
            "origem_extracao": "ofx_manual",
            "usou_ia": False,
        }

        return {
            "status_leitura": status,
            "mensagem_leitura": mensagem,
            "banco": banco,
            "periodo": periodo or "Não identificado",
            "tipo_documento": "Extrato OFX",
            "confianca": 0.99 if status == "ok_completo" else 0.4,
            "origem_banco": origem_banco,
            "origem_periodo": origem_periodo,
            "resumo_estruturado": resumo,
        }

    except Exception as e:
        return {
            "status_leitura": "nao_legivel",
            "mensagem_leitura": f"Erro ao ler OFX manualmente: {e}",
            "banco": "Desconhecido",
            "periodo": "Não identificado",
            "tipo_documento": "Extrato OFX",
            "confianca": 0.0,
            "origem_banco": "erro",
            "origem_periodo": "erro",
            "resumo_estruturado": {
                "sem_movimento": False,
                "saldo_final": None,
                "qtd_movimentacoes": 0,
                "movimentacoes_flat": [],
                "origem_extracao": "ofx_manual_erro",
                "usou_ia": False,
            },
        }


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
        banco, origem_banco = _detectar_instituicao_com_origem("", nome_arquivo, routing_number)

        if banco == "Desconhecido":
            banco = routing_number or "Banco Desconhecido"
            origem_banco = "ofx_routing_number"

        start_date = getattr(extrato, "start_date", None)
        end_date = getattr(extrato, "end_date", None)

        if end_date:
            periodo = formatar_periodo(end_date.month, end_date.year)
            origem_periodo = "ofx_dtend"
        elif start_date:
            periodo = formatar_periodo(start_date.month, start_date.year)
            origem_periodo = "ofx_dtstart"
        else:
            periodo = extrair_periodo_nome_arquivo(nome_arquivo)
            origem_periodo = "nome_arquivo" if periodo else "nao_identificado"

        movimentacoes = []
        for tx in getattr(extrato, "transactions", []) or []:
            valor = float(getattr(tx, "amount", 0) or 0)
            data_tx = getattr(tx, "date", None)
            if data_tx is None:
                continue

            movimentacoes.append({
                "data": data_tx.strftime("%d/%m/%Y"),
                "descricao": compactar_espacos(getattr(tx, "memo", None) or getattr(tx, "payee", None) or "Transação"),
                "valor": abs(valor),
                "natureza": "entrada" if valor >= 0 else "saida",
                "id_transacao": getattr(tx, "id", None),
                "origem": "ofxparse",
            })

        saldo = getattr(extrato, "balance", None)
        saldo_final = float(saldo) if saldo is not None else None

        resumo = {
            "sem_movimento": len(movimentacoes) == 0,
            "saldo_final": saldo_final,
            "conta": getattr(conta, "account_id", None) or getattr(conta, "number", None),
            "bankid": routing_number,
            "qtd_movimentacoes": len(movimentacoes),
            "movimentacoes_flat": movimentacoes,
            "origem_extracao": "ofxparse",
            "usou_ia": False,
        }

        return {
            "status_leitura": "ok_completo" if periodo else "ok_metadados",
            "mensagem_leitura": "Lido perfeitamente via OFX.",
            "banco": banco,
            "periodo": periodo or "Não identificado",
            "tipo_documento": "Extrato OFX",
            "confianca": 0.99 if periodo else 0.75,
            "origem_banco": origem_banco,
            "origem_periodo": origem_periodo,
            "resumo_estruturado": resumo,
        }

    except Exception:
        return None


def processar_ofx(caminho_arquivo: str) -> Dict[str, Any]:
    """Processa OFX/OFC/QFX com ofxparse quando possível e fallback manual sempre."""
    resultado_ofxparse = _processar_ofx_ofxparse(caminho_arquivo)
    if resultado_ofxparse is not None:
        return resultado_ofxparse

    return _processar_ofx_manual(caminho_arquivo)

# ==========================================================
# FALLBACK IA PARA METADADOS
# ==========================================================
def _recorte_texto_para_ia(texto: str, limite_inicio: int = 5000, limite_fim: int = 2500) -> str:
    texto = texto or ""
    if len(texto) <= limite_inicio + limite_fim:
        return texto
    return texto[:limite_inicio] + "\n\n[...]\n\n" + texto[-limite_fim:]


def fallback_ia_metadados(texto: str, nome_arquivo: str = "") -> Dict[str, Any]:
    """
    Fallback opcional. Só tenta se LEITOR_IA_USAR_IA=1 e OPENAI_API_KEY existir.

    Retorna dict vazio se não puder usar IA.
    """
    if not USAR_IA:
        return {}

    if not os.getenv("OPENAI_API_KEY"):
        return {}

    try:
        from openai import OpenAI
    except Exception:
        return {}

    try:
        client = OpenAI()
        recorte = _recorte_texto_para_ia(texto)

        prompt = f"""
Você é um extrator de metadados de extratos financeiros brasileiros.

Responda somente JSON válido com estes campos:
- banco: nome da instituição ou "Desconhecido"
- periodo: competência no formato MM/AAAA ou "Não identificado"
- tipo_documento: "Extrato Bancário", "Extrato de Investimentos", "Extrato de Cotas/Capital", "Extrato OFX" ou "Desconhecido"
- sem_movimento: true/false/null
- confianca: número entre 0 e 1
- motivo: explicação curta

Nome do arquivo: {nome_arquivo}

Texto extraído:
{recorte}
""".strip()

        resp = client.chat.completions.create(
            model=MODELO_IA,
            messages=[
                {"role": "system", "content": "Responda apenas JSON válido, sem markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        conteudo = resp.choices[0].message.content or "{}"
        dados = json.loads(conteudo)
        return dados if isinstance(dados, dict) else {}

    except Exception:
        return {}

# ==========================================================
# PDF PRINCIPAL
# ==========================================================
def calcular_confianca(
    banco: str,
    periodo: Optional[str],
    origem_banco: str,
    origem_periodo: str,
    sem_movimento: bool,
    movimentos_confiaveis: bool,
    usou_ia: bool = False,
) -> float:
    pontos = 0.0

    if banco and banco != "Desconhecido":
        pontos += 0.35
        if origem_banco in {"nome_arquivo", "texto", "bankid"}:
            pontos += 0.10

    if periodo and periodo != "Não identificado":
        pontos += 0.35
        if origem_periodo in {"nome_arquivo", "texto_intervalo_final", "texto_mes_extenso", "ofx_dtend"}:
            pontos += 0.10

    if sem_movimento or movimentos_confiaveis:
        pontos += 0.10

    if usou_ia:
        pontos -= 0.05

    return round(max(0.0, min(0.99, pontos)), 2)


def processar_pdf(caminho_arquivo: str, nome_arquivo: Optional[str] = None) -> Dict[str, Any]:
    nome_arquivo = nome_arquivo or Path(caminho_arquivo).name

    texto, origem_extracao = _extrair_texto_pdf_com_origem(caminho_arquivo)

    if not texto:
        return {
            "status_leitura": "nao_legivel",
            "mensagem_leitura": "PDF sem texto extraível ou ilegível.",
            "banco": "Desconhecido",
            "periodo": "Não identificado",
            "tipo_documento": "Desconhecido",
            "confianca": 0.0,
            "origem_banco": "nao_identificado",
            "origem_periodo": "nao_identificado",
            "resumo_estruturado": {
                "sem_movimento": False,
                "saldo_final": None,
                "qtd_movimentacoes": 0,
                "movimentacoes_flat": [],
                "origem_extracao": origem_extracao,
                "usou_ia": False,
            },
        }

    banco, origem_banco = _detectar_instituicao_com_origem(texto, nome_arquivo)

    periodo_nome = extrair_periodo_nome_arquivo(nome_arquivo)
    if periodo_nome:
        periodo = periodo_nome
        origem_periodo = "nome_arquivo"
    else:
        periodo_texto, origem_periodo_texto = _extrair_periodo_texto_com_origem(texto)
        if periodo_texto:
            periodo = periodo_texto
            origem_periodo = origem_periodo_texto
        else:
            periodo_datas = extrair_periodo_por_datas_movimentacoes(texto)
            periodo = periodo_datas
            origem_periodo = "datas_movimentacoes" if periodo_datas else "nao_identificado"

    tipo_documento = classificar_tipo_documento(texto, nome_arquivo, banco)
    documento_especial = tipo_documento_nao_deve_confiar_movimentacoes(tipo_documento)

    if documento_especial:
        movimentacoes = []
    else:
        movimentacoes = extrair_movimentacoes_genericas(texto, periodo, tipo_documento)

    sem_movimento = detectar_sem_movimento(texto, movimentacoes)

    if sem_movimento:
        movimentacoes = []

    saldo_final = extrair_saldo_final(texto)

    movimentos_confiaveis = movimentacoes_sao_confiaveis(
        movimentacoes,
        texto=texto,
        periodo=periodo,
        tipo_documento=tipo_documento,
    )

    usou_ia = False

    # Fallback IA apenas se metadados essenciais falharem.
    if (banco == "Desconhecido" or not periodo) and USAR_IA:
        ia = fallback_ia_metadados(texto, nome_arquivo)
        if ia:
            usou_ia = True

            if banco == "Desconhecido" and ia.get("banco"):
                banco = ia.get("banco") or banco
                origem_banco = "ia"

            if not periodo and ia.get("periodo") and ia.get("periodo") != "Não identificado":
                periodo = ia.get("periodo")
                origem_periodo = "ia"

            if tipo_documento == "Desconhecido" and ia.get("tipo_documento"):
                tipo_documento = ia.get("tipo_documento") or tipo_documento

            if ia.get("sem_movimento") is True and not movimentacoes:
                sem_movimento = True

    banco_ok = banco and banco != "Desconhecido"
    periodo_ok = periodo and periodo != "Não identificado"

    if banco_ok and periodo_ok:
        if sem_movimento:
            status = "ok_completo"
            mensagem = "Banco, período e ausência de movimentações identificados."
        elif tipo_documento_nao_deve_confiar_movimentacoes(tipo_documento):
            status = "ok_metadados"
            mensagem = f"Banco e período extraídos. Tipo '{tipo_documento}' não usa movimentações por regex genérico."
        elif movimentos_confiaveis:
            status = "ok_completo"
            mensagem = "Banco, período e movimentações extraídos."
        else:
            status = "ok_metadados"
            mensagem = "Banco e período extraídos. Movimentações não foram extraídas com segurança."

    else:
        status = "nao_legivel"
        faltando = []
        if not banco_ok:
            faltando.append("banco")
        if not periodo_ok:
            faltando.append("período")
        mensagem = "Não foi possível identificar " + " e ".join(faltando) + "."

    confianca = calcular_confianca(
        banco=banco,
        periodo=periodo,
        origem_banco=origem_banco,
        origem_periodo=origem_periodo,
        sem_movimento=sem_movimento,
        movimentos_confiaveis=movimentos_confiaveis,
        usou_ia=usou_ia,
    )

    resumo = {
        "sem_movimento": bool(sem_movimento),
        "saldo_final": saldo_final,
        "qtd_movimentacoes": len(movimentacoes),
        "movimentacoes_flat": movimentacoes,
        "movimentacoes_confiaveis": bool(movimentos_confiaveis),
        "origem_extracao": origem_extracao,
        "usou_ia": bool(usou_ia),
    }

    return {
        "status_leitura": status,
        "mensagem_leitura": mensagem,
        "banco": banco,
        "periodo": periodo or "Não identificado",
        "tipo_documento": tipo_documento,
        "confianca": confianca,
        "origem_banco": origem_banco,
        "origem_periodo": origem_periodo,
        "resumo_estruturado": resumo,
    }

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

    return {
        "status_leitura": "nao_legivel",
        "mensagem_leitura": f"Extensão não suportada: {ext}",
        "banco": "Desconhecido",
        "periodo": "Não identificado",
        "tipo_documento": "Desconhecido",
        "confianca": 0.0,
        "origem_banco": "nao_identificado",
        "origem_periodo": "nao_identificado",
        "resumo_estruturado": {
            "sem_movimento": False,
            "saldo_final": None,
            "qtd_movimentacoes": 0,
            "movimentacoes_flat": [],
            "origem_extracao": "extensao_nao_suportada",
            "usou_ia": False,
        },
    }

# ==========================================================
# ORQUESTRADOR MONGO
# ==========================================================
def _status_para_banco(status_leitura: str) -> str:
    if status_leitura == "ok_completo":
        return "processado"
    if status_leitura == "ok_metadados":
        return "processado_com_alerta"
    if status_leitura == "ok":
        return "processado"
    if status_leitura == "revisar":
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

    print(f"\n=== Processando {len(pendentes)} documentos ===\n")

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
                "conteudo": json.dumps(dados.get("resumo_estruturado", {}), ensure_ascii=False),
                "data_processamento": datetime.now(),
            }},
        )

        print(f"  [✓] Status: {db_status} | {dados.get('banco')} | {dados.get('periodo')}")

# ==========================================================
# CLI SIMPLES
# ==========================================================
def _json_default(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return ""


def main() -> None:
    # Uso direto:
    # python workers/leitor_ia.py caminho/arquivo.pdf
    if len(sys.argv) > 1:
        for caminho in sys.argv[1:]:
            resultado = processar_documento(caminho, Path(caminho).name)
            print(json.dumps(resultado, indent=4, ensure_ascii=False, default=_json_default))
        return

    processar_lote_documentos()


if __name__ == "__main__":
    main()