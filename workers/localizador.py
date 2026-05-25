import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Setup de caminhos para importação correta
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
RAIZ_PROJETO = os.path.dirname(DIRETORIO_ATUAL)

if RAIZ_PROJETO not in sys.path:
    sys.path.append(RAIZ_PROJETO)

load_dotenv(os.path.join(RAIZ_PROJETO, ".env"))

from services.mongo import clientes_col, solicitacoes_col, arquivos_col
from services.db_dominio import get_cnpj_dominio

BASE_PATH = os.getenv("BASE_EXTRATOS_PATH")


def obter_mes_apuracao(data_base=None):
    """Retorna o último mês no formato MM.YYYY."""
    hoje = data_base or datetime.now()
    primeiro_dia_mes_atual = hoje.replace(day=1)
    ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
    return ultimo_dia_mes_anterior.strftime("%m.%Y")


EXTENSOES_EXTRATO = {".pdf", ".ofx", ".ofc", ".qfx"}


def listar_arquivos_extrato(pasta_extrato: Path):
    """
    Lista arquivos de extrato aceitando PDF, OFX, OFC e QFX.
    No Linux, glob('*.pdf') não encontra .PDF maiúsculo, por isso usamos suffix.lower().
    """
    arquivos = []

    for arquivo in pasta_extrato.iterdir():
        if not arquivo.is_file():
            continue

        if arquivo.suffix.lower() not in EXTENSOES_EXTRATO:
            continue

        arquivos.append(arquivo)

    return sorted(arquivos, key=lambda p: p.name.lower())


def normalizar_caminho(caminho: Path):
    """
    Padroniza o caminho para evitar diferenças pequenas de representação.
    """
    return str(caminho.resolve())


def buscar_arquivo_existente(solicitacao_id, caminho_str, nome_arquivo):
    """
    Evita duplicidade, mas também permite recuperar casos antigos.
    Primeiro tenta pelo caminho completo.
    Depois tenta pela combinação solicitação + nome do arquivo.
    """
    existente = arquivos_col.find_one({
        "caminho_completo": caminho_str
    })

    if existente:
        return existente

    existente = arquivos_col.find_one({
        "solicitacao_id": solicitacao_id,
        "nome_arquivo": nome_arquivo
    })

    return existente


def varrer_rede_extratos():
    print(f"\n[{datetime.now():%d/%m/%Y %H:%M:%S}] Iniciando varredura da rede...")

    if not BASE_PATH:
        print("ERRO: BASE_EXTRATOS_PATH não está configurado no .env")
        return

    base_dir = Path(BASE_PATH)

    if not base_dir.exists():
        print(f"ERRO: Caminho base não encontrado na rede: {base_dir}")
        return

    mes_alvo = obter_mes_apuracao()
    print(f"📌 Mês de Apuração Alvo: {mes_alvo}")

    novos_arquivos = 0
    arquivos_ja_existentes = 0
    solicitacoes_registradas = 0
    pastas_extrato_lidas = 0

    for pasta_empresa in base_dir.iterdir():
        if not pasta_empresa.is_dir() or " - " not in pasta_empresa.name:
            continue

        codigo_str, nome_empresa = pasta_empresa.name.split(" - ", 1)

        try:
            codigo_dominio = int(codigo_str.strip())
        except ValueError:
            continue

        pasta_mes = pasta_empresa / mes_alvo

        if not pasta_mes.exists():
            continue

        cliente = clientes_col.find_one({
            "codigo_dominio": codigo_dominio
        })

        if not cliente:
            cnpj = get_cnpj_dominio(codigo_dominio)

            print(
                f"✨ Novo cliente cadastrado automaticamente: "
                f"{codigo_dominio} - {nome_empresa} (CNPJ: {cnpj or 'Vazio'})"
            )

            cliente_id = clientes_col.insert_one({
                "codigo_dominio": codigo_dominio,
                "nome_empresa": nome_empresa,
                "cnpj": cnpj,
                "ativo": True,
                "data_cadastro": datetime.now()
            }).inserted_id
        else:
            cliente_id = cliente["_id"]

        for pasta_solicitacao in pasta_mes.iterdir():
            if not pasta_solicitacao.is_dir():
                continue

            numero_solicitacao = pasta_solicitacao.name
            pasta_extrato = pasta_solicitacao / "EXTRATO"

            if not pasta_extrato.exists():
                continue

            pastas_extrato_lidas += 1

            solicitacao = solicitacoes_col.find_one({
                "numero_solicitacao": numero_solicitacao,
                "cliente_id": cliente_id
            })

            if solicitacao:
                solicitacao_id = solicitacao["_id"]
            else:
                data_pasta = datetime.fromtimestamp(pasta_solicitacao.stat().st_mtime)

                solicitacao_id = solicitacoes_col.insert_one({
                    "numero_solicitacao": numero_solicitacao,
                    "mes_referencia": mes_alvo,
                    "cliente_id": cliente_id,
                    "caminho_pasta": str(pasta_solicitacao),
                    "data_importacao": data_pasta,
                    "validado": False
                }).inserted_id

                solicitacoes_registradas += 1

            arquivos_encontrados = listar_arquivos_extrato(pasta_extrato)

            if arquivos_encontrados:
                print(
                    f"\n📁 [{codigo_dominio}] Solicitação {numero_solicitacao}: "
                    f"{len(arquivos_encontrados)} PDF(s) encontrado(s) na pasta EXTRATO"
                )

            for arquivo_pdf in arquivos_encontrados:
                caminho_str = normalizar_caminho(arquivo_pdf)

                existente = buscar_arquivo_existente(
                    solicitacao_id=solicitacao_id,
                    caminho_str=caminho_str,
                    nome_arquivo=arquivo_pdf.name
                )

                if existente:
                    arquivos_ja_existentes += 1
                    continue

                arquivos_col.insert_one({
                    "solicitacao_id": solicitacao_id,
                    "cliente_id": cliente_id,
                    "numero_solicitacao": numero_solicitacao,
                    "nome_arquivo": arquivo_pdf.name,
                    "extensao": arquivo_pdf.suffix.lower(),
                    "caminho_completo": caminho_str,
                    "status": "pendente",
                    "data_leitura": datetime.fromtimestamp(arquivo_pdf.stat().st_mtime),
                    "data_cadastro": datetime.now()
                })

                novos_arquivos += 1

                print(f"  📄 Novo extrato pendente: [{codigo_dominio}] {arquivo_pdf.name}")

    print("\n✅ Varredura concluída!")
    print(f"   Solicitações novas: {solicitacoes_registradas}")
    print(f"   Pastas EXTRATO lidas: {pastas_extrato_lidas}")
    print(f"   PDFs novos enfileirados: {novos_arquivos}")
    print(f"   PDFs já existentes ignorados: {arquivos_ja_existentes}")


if __name__ == "__main__":
    varrer_rede_extratos()