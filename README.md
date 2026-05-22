# Extrato Contábil

Sistema interno para conferência e controle de extratos bancários enviados por clientes.

O projeto organiza os arquivos recebidos em pastas de pré-triagem, identifica os extratos por empresa e competência, realiza leitura automática dos documentos e permite que o usuário confira, visualize e corrija informações como banco, período e observações internas.

O objetivo principal é apoiar o setor contábil na validação dos documentos enviados pelos clientes, reduzindo conferências manuais em pastas de rede e centralizando o acompanhamento em uma interface web.

## Funcionalidades

- Localização automática de extratos em pasta de rede ou pasta local configurada.
- Cadastro automático de clientes com base no código da empresa(Domínio).
- Integração com o banco do Domínio para consulta de dados da empresa.
- Leitura automática de PDFs de extratos bancários.
- Identificação de banco, período e tipo de documento.
- Tela de acompanhamento por cliente e competência.
- Visualização do PDF original diretamente pela interface.
- Edição manual de banco, período e observações.
- Registro da última edição realizada por usuário.
- Histórico interno de alterações nos arquivos.
- Validação de lote de extratos por solicitação.
- Exportação de relatório em Excel formatado.
- Autenticação com JWT.

## Estrutura geral do fluxo

1. O localizador percorre a pasta configurada em `BASE_EXTRATOS_PATH`.
2. Os arquivos encontrados são registrados no MongoDB como pendentes.
3. O leitor processa os arquivos e tenta identificar banco, período e conteúdo.
4. O usuário acessa a interface para conferir os documentos.
5. Caso necessário, o usuário corrige banco, período ou observação.
6. O sistema registra a edição e permite validar o lote.
7. O relatório pode ser exportado em Excel.

## Requisitos

- Python 3.11 ou superior
- MongoDB
- Acesso à pasta de rede dos extratos
- Acesso ao banco do Domínio, quando aplicável
- Node.js, caso o frontend esteja separado em React/Vite

## Instalação do backend

Clone o repositório:

```bash
git clone https://seu-repositorio.git
cd ExtratoContabil
````

Crie e ative o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Exemplo de `.env`

Crie um arquivo `.env` na raiz do projeto com as variáveis abaixo:

```env
MONGO_URI=
MONGO_DB=

JWT_SECRET_KEY=

OPENAI_API_KEY=

SMTP_SERVER=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=

APP_FRONTEND_URL=

BASE_EXTRATOS_PATH=

DOMINIO_HOST=
DOMINIO_PORT=
DOMINIO_DB=
DOMINIO_USER=
DOMINIO_PASSWORD=
```

## Execução

Para iniciar a API Flask:

```bash
source .venv/bin/activate
python app.py
```

Para executar a varredura dos extratos:

```bash
python localizador.py
```

Para processar os documentos pendentes:

```bash
python leitor_ia.py
```

Caso o frontend esteja em React/Vite:

```bash
npm install
npm run dev
```

## Observações

* O sistema depende do caminho configurado em `BASE_EXTRATOS_PATH` para localizar os arquivos.
* A máquina que executa o backend precisa ter acesso à pasta de rede dos extratos.
* A leitura automática pode identificar banco e período, mas o usuário pode corrigir manualmente quando necessário.
* As alterações manuais ficam registradas para controle interno.

## Licença

Este software é de uso interno e possui todos os direitos reservados.

É proibida a cópia, distribuição, modificação ou uso não autorizado deste sistema sem autorização expressa do responsável pelo projeto.

## Contato

Para dúvidas, suporte ou solicitações de uso, entre em contato com o responsável pelo sistema.
