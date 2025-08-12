# Validação de E-mails com Geração de Relatório CSV

## Objetivo

Este projeto implementa um script em Python que lê uma lista de e-mails, valida a sintaxe e verifica a existência do domínio para cada um. Ao final, gera um arquivo CSV classificando os e-mails como "Válido" ou "Inválido", com um motivo para cada caso.

---

## Funcionalidades

- Leitura de e-mails a partir de arquivo texto (`emails.txt`).
- Validação da sintaxe dos e-mails usando a biblioteca `email_validator`.
- Validação da existência do domínio através da consulta DNS (registros MX, e fallback para A/AAAA).
- Geração de relatório CSV com colunas: `email`, `status` e `motivo`.
- Processamento paralelo para melhor desempenho em listas grandes.
- Cache para evitar múltiplas consultas DNS ao mesmo domínio.
- Tratamento de erros robusto e mensagens informativas no console.

---

## Pré-requisitos

- Python 3.6 ou superior
- Bibliotecas Python:
  ```bash
  pip install email_validator dnspython

## Como usar
Prepare seu arquivo emails.txt com uma lista de e-mails, um por linha. Linhas vazias ou iniciadas com # serão ignoradas.

Execute o script:

python validate_emails.py emails.txt validacao_emails.csv

O resultado será salvo no arquivo validacao_emails.csv.

Exemplo de saída (validacao_emails.csv)
| email                                         | status   | motivo                           |
| --------------------------------------------- | -------- | -------------------------------- |
| [teste@exemplo.com](mailto:teste@exemplo.com) | Válido   | mx1.exemplo.com, mx2.exemplo.com |
| invalido-email.com                            | Inválido | Sintaxe inválida: Missing '@'    |
| usuario\@dominio.inexistente123               | Inválido | Domínio não encontrado           |


## Estrutura do Código
ler_emails(path): lê e-mails do arquivo de entrada.

validar_sintaxe_email(email): valida a sintaxe de um e-mail.

validar_dominio_email(domain): verifica se o domínio tem registros DNS válidos.

processar_email(email, cache, lock): função principal que valida o e-mail (sintaxe + domínio), usando cache e controle de concorrência.

gerar_arquivo_csv(caminho_saida, dados): grava os resultados no CSV.

main(input_file, output_file, workers): orquestra a execução do script.
