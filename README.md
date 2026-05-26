# Extrato Contábil

Sistema interno para conferência e controle de extratos bancários enviados por clientes.

O projeto organiza os arquivos recebidos em pastas de pré-triagem, identifica os documentos por empresa e competência, realiza leitura automática de metadados e permite que o usuário confira, visualize, baixe e corrija informações como banco, período e observações internas.

O objetivo principal é apoiar o setor contábil na validação dos documentos enviados pelos clientes, reduzindo conferências manuais em pastas de rede e centralizando o acompanhamento em uma interface web.

> Importante: o sistema não substitui a conferência contábil do usuário. A leitura automática serve para organizar os documentos e identificar informações essenciais, como banco, período e tipo de documento. A interpretação final do conteúdo permanece sob responsabilidade do analista.

---

## Funcionalidades

- Localização automática de extratos em pasta de rede ou pasta local configurada.
- Cadastro automático de clientes com base no código da empresa.
- Integração com o banco do Domínio para consulta de dados da empresa, quando aplicável.
- Registro de solicitações e arquivos no MongoDB.
- Leitura automática de PDFs para identificação de metadados.
- Suporte a arquivos estruturados `.ofx`, `.ofc` e `.qfx`.
- Identificação de banco, período e tipo de documento.
- Identificação simples de documentos sem movimento, quando a informação estiver clara.
- Tela de dashboard com visão geral da competência.
- Tela de acompanhamento por cliente e competência.
- Tela de detalhes do cliente com todos os arquivos encontrados no mês.
- Visualização de PDFs diretamente pela interface.
- Download de arquivos originais não visualizáveis no navegador, como OFX/OFC/QFX.
- Edição manual de banco, período e observações.
- Registro da última edição realizada por usuário.
- Histórico interno de alterações nos arquivos.
- Validação de lote de extratos por solicitação.
- Exportação de relatório em Excel formatado.
- Autenticação com JWT.

---

## Documentação operacional

Para entender o fluxo de telas, interpretação do dashboard, leitura automática e regras de conferência manual, acesse:

```text
MANUAL.md
```

---

## Estrutura geral do fluxo

1. O localizador percorre a pasta configurada em `BASE_EXTRATOS_PATH`.
2. Os arquivos encontrados são registrados no MongoDB como pendentes.
3. O leitor processa os arquivos e tenta identificar banco, período e tipo de documento.
4. Em arquivos OFX/OFC/QFX, o sistema usa leitura estruturada quando possível.
5. Em PDFs, o sistema tenta ler o texto nativo e, se necessário, pode usar OCR.
6. O usuário acessa a interface para conferir os documentos.
7. Caso necessário, o usuário corrige banco, período ou observação.
8. O sistema registra a edição e mantém histórico interno.
9. O usuário pode validar o lote.
10. O relatório pode ser exportado em Excel.

---

## Requisitos

- Python 3.11 ou superior.
- MongoDB.
- Node.js e NPM para o frontend React/Vite.
- Acesso à pasta de rede dos extratos.
- Acesso ao banco do Domínio, quando aplicável.
- Tesseract OCR, se houver necessidade de leitura de PDFs digitalizados como imagem.

### Observação sobre OCR

O Tesseract só é necessário para PDFs que não possuem texto nativo. Caso a maioria dos arquivos já tenha texto selecionável, o sistema pode funcionar sem OCR, mas terá menor capacidade de leitura em documentos escaneados.

Configure a variável `TESSERACT_CMD` no `.env` se o executável não estiver no PATH do sistema.

---

## Instalação do backend

Clone ou copie o projeto para a máquina onde ele será executado:

```bash
cd ExtratoContabil
```

Crie o ambiente virtual.

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, libere apenas para o terminal atual:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Instalação do frontend

Entre na pasta do frontend:

```bash
cd frontend
```

Instale as dependências:

```bash
npm install
```

Se necessário, instale também os pacotes usados na interface:

```bash
npm install lucide-react
```

Para Tailwind em projeto Vite moderno:

```bash
npm install tailwindcss @tailwindcss/vite
```

---

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

APP_FRONTEND_URL=


# BASE_EXTRATOS_PATH=
BASE_EXTRATOS_PATH=

DOMINIO_HOST=
DOMINIO_PORT=
DOMINIO_DB=
DOMINIO_USER=
DOMINIO_PASSWORD=

```

### Observação sobre OpenAI

A integração com OpenAI deve ser considerada opcional. O fluxo principal do sistema não depende dela. Por padrão, recomenda-se manter:

```env
LEITOR_IA_USAR_IA=0
```

Caso futuramente a leitura por IA externa seja ativada, será necessário configurar chave de API e controle de custos/limites.

---

## Execução do backend

Para iniciar a API Flask:

```bash
python app.py
```

Em ambiente de rede, o Flask deve estar configurado para escutar em todas as interfaces:

```python
app.run(debug=True, host="0.0.0.0", port=5000)
```

Com isso, a API poderá ser acessada pelo IP da máquina, por exemplo:

```text
http://10.0.0.62:5000
```

---

## Execução do frontend

Na pasta `frontend`:

```bash
npm run dev -- --host
```

O Vite informará os endereços disponíveis, por exemplo:

```text
Local:   http://localhost:5174/
Network: http://10.0.0.62:5174/
```

Para acessar de outro computador da rede, use o endereço `Network`.

---

## Configuração do frontend para acessar a API

O arquivo de serviço da API deve apontar para o backend.

Exemplo em `frontend/src/services/api.js`:

```js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://10.0.0.62:5000/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
```

Em produção ou em ambiente com IP variável, recomenda-se usar `.env` no frontend:

```env
VITE_API_URL=http://10.0.0.62:5000/api
```

E no `api.js`:

```js
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
});
```

---

## Execução do motor de extratos

Para rodar o processo contínuo que localiza e processa documentos:

```bash
python workers/motor_extratos.py
```

No Windows:

```powershell
python workers\motor_extratos.py
```

Se houver opção de execução imediata no motor:

```bash
python workers/motor_extratos.py --run-now
```

O motor deve ser executado em terminal separado do backend e do frontend.

---

## Execução manual dos scripts

Caso precise rodar os scripts manualmente apenas uma vez:

```bash
python workers/localizador.py
python workers/leitor_ia.py
```

Ajuste os caminhos conforme a estrutura real do projeto.

---

## Portas e acesso em rede

Por padrão:

- Backend Flask: `5000`
- Frontend Vite: `5173` ou `5174`

Se outra máquina não conseguir acessar, libere as portas no firewall da VM/servidor.

No Windows PowerShell como administrador:

```powershell
netsh advfirewall firewall add rule name="ExtratoContabil Flask 5000" dir=in action=allow protocol=TCP localport=5000
netsh advfirewall firewall add rule name="ExtratoContabil Vite 5174" dir=in action=allow protocol=TCP localport=5174
```

---

## Observações importantes

- O sistema depende do caminho configurado em `BASE_EXTRATOS_PATH` para localizar os arquivos.
- A máquina que executa o backend precisa ter acesso à pasta de rede dos extratos.
- O backend precisa conseguir se comunicar com o MongoDB.
- A integração com o banco do Domínio depende de driver, rede e credenciais corretas.
- A leitura automática pode identificar banco, período, tipo e ausência de movimento quando possível.
- O usuário pode corrigir manualmente banco, período e observação.
- As alterações manuais ficam registradas para controle interno.
- PDFs são visualizados no navegador.
- Arquivos estruturados como OFX/OFC/QFX são baixados para conferência externa.

---

## Limitações conhecidas

- O sistema não realiza conciliação bancária completa.
- O sistema não interpreta contabilmente todos os lançamentos de PDFs.
- PDFs digitalizados podem depender de OCR e ter menor qualidade de leitura.
- Arquivos enviados fora do padrão de pasta podem precisar de revisão manual.
- A identificação de banco/período pode falhar em documentos muito ruins ou sem informações claras.

---
