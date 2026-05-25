import time
import traceback
from datetime import datetime

from localizador import varrer_rede_extratos
from leitor_ia import processar_lote_documentos


INTERVALO_MINUTOS = 60


def executar_ciclo():
    print("\n" + "=" * 80)
    print(f"[{datetime.now():%d/%m/%Y %H:%M:%S}] Iniciando ciclo dos extratos")
    print("=" * 80)

    try:
        print("\n[1/2] Rodando localizador...")
        varrer_rede_extratos()
        print("[OK] Localizador finalizado.")

    except Exception:
        print("[ERRO] Falha no localizador:")
        traceback.print_exc()

    try:
        print("\n[2/2] Rodando leitor_ia...")
        processar_lote_documentos()
        print("[OK] Leitor IA finalizado.")

    except Exception:
        print("[ERRO] Falha no leitor_ia:")
        traceback.print_exc()

    print(f"\n[{datetime.now():%d/%m/%Y %H:%M:%S}] Ciclo finalizado.")


def main():
    print("Motor de extratos iniciado.")
    print(f"Intervalo entre ciclos: {INTERVALO_MINUTOS} minuto(s).")

    while True:
        executar_ciclo()

        print(
            f"\nAguardando {INTERVALO_MINUTOS} minuto(s) "
            "para a próxima varredura..."
        )

        time.sleep(INTERVALO_MINUTOS * 60)


if __name__ == "__main__":
    main()