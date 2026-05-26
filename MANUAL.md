# Manual de Instruções – Extrato Contábil

Este manual orienta o uso operacional do sistema **Extrato Contábil**, utilizado para acompanhar, conferir e validar extratos bancários enviados pelos clientes.

O sistema centraliza os documentos localizados na rede, identifica informações básicas dos arquivos e permite que o usuário faça a conferência final diretamente pela interface.

> O sistema não substitui a análise contábil do usuário.  
> A leitura automática serve como apoio para identificar banco, período, tipo de documento e algumas situações simples. A conferência final do conteúdo continua sendo responsabilidade do analista.

---

## 1. Objetivo do sistema

O Extrato Contábil foi criado para facilitar a rotina de conferência de extratos bancários recebidos dos clientes.

Com ele, o usuário consegue:

- acompanhar quais empresas enviaram extratos;
- verificar quais empresas ainda estão pendentes;
- visualizar os arquivos recebidos por competência;
- conferir banco e período identificados automaticamente;
- corrigir informações quando necessário;
- registrar observações internas;
- validar o lote da empresa;
- exportar relatório em Excel.

O foco principal do sistema é **organizar e centralizar a conferência**, evitando que o usuário precise procurar manualmente os arquivos em diversas pastas de rede.

---

## 2. Como o sistema trabalha

O sistema segue este fluxo geral:

1. O robô localiza arquivos de extratos na pasta configurada.
2. Os arquivos são vinculados à empresa e à competência.
3. O leitor automático tenta identificar banco, período e tipo do documento.
4. O usuário acessa a tela de acompanhamento.
5. O usuário abre os detalhes da empresa.
6. O usuário confere os arquivos.
7. Se necessário, corrige banco, período ou observação.
8. O usuário valida o lote da empresa na competência.
9. O relatório pode ser exportado em Excel.

---

## 3. Tipos de arquivo aceitos

O sistema pode trabalhar com arquivos como:

| Tipo | Comportamento |
|---|---|
| PDF | Pode ser visualizado diretamente no navegador |
| OFX | É lido como arquivo estruturado e pode ser baixado |
| OFC | É lido como arquivo estruturado e pode ser baixado |
| QFX | É lido como arquivo estruturado e pode ser baixado |

Arquivos PDF são usados principalmente para conferência visual.

Arquivos OFX/OFC/QFX costumam conter informações mais estruturadas, mas ainda assim devem ser conferidos pelo usuário quando necessário.

---

## 4. Leitura automática

A leitura automática tenta identificar informações básicas do documento.

Ela pode identificar:

- banco;
- período;
- tipo do documento;
- ausência de movimentação, quando estiver clara no arquivo;
- modo de leitura, como PDF ou OFX.

A leitura automática **não garante**:

- conciliação bancária completa;
- leitura de todos os lançamentos do PDF;
- interpretação contábil dos valores;
- classificação definitiva de entradas e saídas;
- validação fiscal ou contábil.

Por isso, quando houver dúvida, o usuário deve abrir o arquivo original e fazer a conferência manual.

---

## 5. Tela de login

A tela de login permite o acesso ao sistema.

O usuário deve informar suas credenciais e entrar na plataforma.

Se a sessão expirar, o sistema pode redirecionar automaticamente para a tela de login.

---

## 6. Dashboard

O dashboard apresenta uma visão geral da competência selecionada.

Nele, o usuário pode acompanhar:

- total de empresas da carteira;
- empresas com arquivos enviados;
- empresas sem arquivos enviados;
- volume de arquivos ou solicitações processadas;
- gráficos e indicadores gerais;
- listas exportáveis, quando disponíveis.

O dashboard serve para uma visão gerencial da competência.

---

## 7. Tela de acompanhamento

A tela de acompanhamento é a central de trabalho do usuário.

Ela mostra as empresas da competência selecionada e seus respectivos status.

Normalmente são exibidas informações como:

- código da empresa;
- CNPJ;
- razão social;
- status;
- quantidade de arquivos recebidos;
- último envio;
- indicação de validação.

Ao clicar em uma empresa, o sistema abre a tela de detalhes do cliente.

---

## 8. Abas de acompanhamento

A tela pode separar os clientes em abas, como:

| Aba | Significado |
|---|---|
| Pendentes | Empresas que ainda precisam de conferência ou validação |
| Validadas | Empresas que já tiveram o lote validado |

A quantidade exibida em cada aba ajuda o usuário a acompanhar o andamento da competência.

---

## 9. Filtros e busca

A tela de acompanhamento permite filtrar e pesquisar empresas.

O usuário pode:

- selecionar a competência;
- pesquisar por nome da empresa;
- pesquisar por código;
- pesquisar por CNPJ;
- ordenar ou navegar entre registros, conforme os controles disponíveis.

Esses filtros ajudam a localizar rapidamente a empresa que precisa ser conferida.

---

## 10. Tela de detalhes do cliente

A tela de detalhes mostra os arquivos encontrados para uma empresa em uma competência.

Nessa tela, o usuário visualiza:

- nome da empresa;
- CNPJ;
- código;
- quantidade de solicitações;
- quantidade de arquivos identificados;
- quantidade de arquivos editados;
- lista de arquivos recebidos;
- banco e período de cada arquivo;
- situação da leitura;
- ações disponíveis.

Quando uma empresa possui mais de uma solicitação no mesmo mês, o sistema pode agrupar os arquivos na mesma tela de detalhes.

---

## 11. Solicitações

Uma empresa pode ter uma ou mais solicitações na mesma competência.

Na tela de detalhes, o sistema exibe a quantidade de solicitações encontradas.

Para o usuário, o mais importante é o conjunto de arquivos da empresa naquela competência.

Ou seja:

```text
Empresa + competência = lote de conferência
```

Mesmo que existam várias solicitações, a conferência é feita olhando o conjunto de arquivos exibidos na tela.

---

## 12. Situação dos arquivos

Cada arquivo pode aparecer com uma situação visual.

| Situação | Significado | Ação esperada |
|---|---|---|
| Identificado | Banco e período foram identificados | Conferir visualmente se necessário |
| OFX lido | Arquivo estruturado foi lido | Conferir se banco e período fazem sentido |
| Sem movimento | O sistema identificou ausência de movimentação | Abrir o arquivo e confirmar visualmente |
| Conferir | Banco ou período não foram identificados com segurança | Abrir o arquivo, corrigir e salvar |
| Editado | O arquivo teve informação alterada manualmente | Verificar histórico se necessário |

---

## 13. Arquivos identificados

Quando o sistema marca um arquivo como **Identificado**, significa que ele conseguiu localizar as informações principais, como banco e período.

Mesmo assim, o usuário pode abrir o arquivo original para confirmar o conteúdo.

Esse status não significa que o sistema interpretou todos os lançamentos do extrato.

---

## 14. Arquivos para conferir

Quando um arquivo aparece como **Conferir**, significa que alguma informação importante não foi identificada com segurança.

Exemplos:

- banco desconhecido;
- período não identificado;
- documento com baixa qualidade;
- arquivo fora do padrão;
- leitura automática insuficiente.

Nesses casos, o usuário deve:

1. abrir o arquivo original;
2. verificar banco e período;
3. preencher ou corrigir os campos;
4. adicionar observação, se necessário;
5. salvar as alterações.

---

## 15. Arquivo sem movimento

Quando o sistema identifica que um arquivo parece estar sem movimentação, ele pode marcar a situação como **Sem movimento**.

Essa indicação serve para agilizar a conferência, mas o usuário deve abrir o arquivo original quando precisar confirmar a informação.

Exemplos de situações que podem gerar essa marcação:

- extrato informa que não houve transações;
- extrato informa ausência de lançamentos;
- extrato indica que não há movimentações no período.

---

## 16. Abrir ou baixar arquivo original

Na tela de detalhes, o usuário pode abrir o arquivo original.

O comportamento depende do tipo de arquivo:

| Tipo | Ação |
|---|---|
| PDF | Abre no navegador |
| OFX/OFC/QFX | Baixa o arquivo |
| Outros | Baixa o arquivo |

PDFs são abertos para conferência visual.

Arquivos OFX/OFC/QFX não são documentos visuais como PDF, por isso são baixados para abertura em outro programa quando necessário.

---

## 17. Visualizar e editar informações do arquivo

Ao clicar para visualizar ou editar um arquivo, o sistema abre uma janela com as informações daquele documento.

Nessa janela, o usuário pode ver e alterar:

- banco;
- período;
- observação interna.

Também pode consultar a leitura automática, quando disponível.

---

## 18. Campo Banco

O campo **Banco** indica qual instituição financeira foi identificada no documento.

Exemplos:

- Banco Inter;
- Itaú;
- Bradesco;
- Caixa Econômica Federal;
- Banco do Brasil;
- Santander;
- Sicoob;
- Sicredi;
- Nubank;
- C6 Bank;
- XP Investimentos;
- Stone;
- PagSeguro.

Se o banco estiver errado ou desconhecido, o usuário pode corrigir manualmente.

---

## 19. Campo Período

O campo **Período** indica a competência do extrato.

O formato recomendado é:

```text
MM/AAAA
```

Exemplo:

```text
04/2026
```

Quando o período estiver incorreto ou não identificado, o usuário deve abrir o arquivo original e corrigir manualmente.

---

## 20. Observação interna

O campo de observação é livre e pode ser usado para registrar informações úteis para a conferência.

Exemplos:

- cliente enviou arquivo errado;
- extrato sem movimento;
- documento ilegível;
- período corrigido manualmente;
- banco corrigido manualmente;
- necessário solicitar novo arquivo ao cliente;
- arquivo conferido manualmente;
- documento não corresponde à competência.

A observação fica registrada junto ao arquivo.

---

## 21. Salvar alterações

Após alterar banco, período ou observação, o usuário deve clicar em **Salvar alterações**.

Quando a alteração é salva, o sistema registra a última edição realizada no arquivo.

Na tela, o usuário consegue visualizar:

- quem realizou a última edição;
- data e hora da última edição.

Esse registro ajuda a identificar se o arquivo já foi revisado manualmente por algum usuário.

---

## 22. Última edição do arquivo

Quando um arquivo é editado manualmente, a tela exibe a informação da última edição realizada.

Exemplo:

```text
Última edição por ADMIN em 26/05/2026 10:57

---

## 23. Validação de lote

A validação de lote indica que o usuário revisou os documentos da empresa na competência selecionada e considera a etapa concluída.

Quando houver mais de uma solicitação para o mesmo cliente e competência, o sistema agrupa os arquivos na tela de detalhes e a validação representa o conjunto daquele cliente/mês.

Antes de validar, recomenda-se:

1. verificar se existem arquivos marcados como **Conferir**;
2. abrir os arquivos originais quando necessário;
3. corrigir banco e período;
4. adicionar observações relevantes;
5. salvar as alterações;
6. clicar em **Validar lote**.

Se ainda houver arquivos para conferência, o sistema pode alertar antes de concluir a validação.

---

## 24. Exportação em Excel

A tela de detalhes permite exportar um relatório em Excel.

O relatório pode conter:

- solicitação;
- nome do extrato;
- banco;
- período;
- observação.

Quando houver mais de uma solicitação para o mesmo cliente e competência, o relatório pode reunir todos os arquivos exibidos na tela de detalhes.

A exportação pode ser usada para:

- conferência interna;
- registro do fechamento;
- acompanhamento do responsável;
- documentação do processo.

---

## 25. Fluxo recomendado de uso

Para uma conferência organizada, recomenda-se seguir este fluxo:

1. Acessar o sistema.
2. Abrir a tela de acompanhamento.
3. Selecionar a competência desejada.
4. Localizar a empresa.
5. Entrar nos detalhes do cliente.
6. Verificar os arquivos identificados.
7. Filtrar arquivos para conferir, se houver.
8. Abrir os arquivos originais.
9. Corrigir banco ou período, se necessário.
10. Registrar observações internas.
11. Salvar alterações.
12. Validar o lote.
13. Exportar o Excel, se necessário.

---

## 26. Cenários comuns

### 26.1. Banco desconhecido

**O que significa:**  
O sistema não conseguiu identificar o banco do documento.

**O que fazer:**  
Abrir o arquivo original, identificar o banco visualmente e preencher o campo manualmente.

---

### 26.2. Período não identificado

**O que significa:**  
O sistema não conseguiu localizar a competência do extrato.

**O que fazer:**  
Abrir o arquivo original, verificar o período e preencher no formato `MM/AAAA`.

---

### 26.3. Arquivo OFX não abre no navegador

**O que significa:**  
OFX não é um documento visual como PDF.

**O que fazer:**  
O arquivo deve ser baixado e aberto em programa compatível, se necessário.

---

### 26.4. PDF não abre

**Possíveis causas:**

- o arquivo não existe mais no caminho original;
- a máquina do backend não tem acesso à pasta de rede;
- o caminho salvo no banco está incorreto;
- o token de sessão expirou;
- o navegador bloqueou a abertura de nova aba.

**O que fazer:**  
Verificar se o arquivo existe na rede e tentar acessar novamente. Se o problema continuar, solicitar apoio técnico.

---

### 26.5. Documento escaneado ou com baixa qualidade

**O que significa:**  
O leitor automático pode não conseguir identificar as informações.

**O que fazer:**  
Abrir o arquivo original, preencher os dados manualmente e registrar observação.

---

### 26.6. Arquivo marcado como sem movimento

**O que significa:**  
O sistema encontrou indicação de ausência de movimentação.

**O que fazer:**  
Abrir o arquivo original e confirmar visualmente. Se estiver correto, seguir com a validação.

---

## 27. Boas práticas

- Conferir todos os arquivos marcados como **Conferir**.
- Não validar lote sem revisar documentos duvidosos.
- Usar observações internas sempre que houver algo fora do padrão.
- Corrigir banco e período antes de validar.
- Abrir o arquivo original quando houver dúvida.
- Não confiar apenas na leitura automática para análise contábil.
- Validar o lote somente após a conferência dos arquivos da empresa.
- Exportar o Excel quando precisar registrar ou compartilhar a conferência.
- Conferir a indicação de última edição para identificar arquivos que já foram ajustados manualmente.

---

## 28. Limitações do sistema

O sistema não realiza:

- conciliação bancária automática completa;
- classificação contábil definitiva;
- validação fiscal;
- leitura perfeita de documentos escaneados;
- interpretação completa de todos os lançamentos de PDF;
- substituição da conferência humana.

O sistema realiza:

- localização de arquivos;
- organização por empresa e competência;
- leitura automática de metadados;
- apoio à conferência;
- registro de correções;
- histórico de alterações;
- validação de lote;
- exportação de relatório.

---

## 29. Responsabilidade do usuário

A responsabilidade final pela conferência dos documentos é do usuário responsável pelo fechamento contábil.

O sistema deve ser usado como ferramenta de apoio para reduzir trabalho manual, padronizar a conferência e centralizar informações relevantes.
