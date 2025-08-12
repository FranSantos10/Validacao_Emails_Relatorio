#!/usr/bin/env python3
import csv
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from email_validator import validate_email, EmailNotValidError
import dns.resolver
import threading

# Configura o logging para mostrar mensagens no console
logging.basicConfig(level=logging.INFO, format="%(message)s")

def ler_emails(path):
    """
    Lê os emails de um arquivo texto.
    Ignora linhas vazias e comentários (linhas que começam com '#').
    """
    try:
        with open(path, encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:   
        logging.error(f"Arquivo não encontrado: {path}")
        sys.exit(1) # Sai do programa com erro
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo {path}: {e}") 
        sys.exit(1)

def validar_sintaxe_email(email):
    """
    Valida a sintaxe do email usando a biblioteca email_validator.
    Retorna (bool, email_normalizado, motivo_erro).
    """
    try:
        v = validate_email(email)
        normalized = v.email # email em formato normalizado
        return True, normalized, ""
    except EmailNotValidError as e:
        return False, email, str(e)

def validar_dominio_email(domain, timeout=3.0):
    """
    Verifica se o domínio possui registros MX ou A/AAAA para validar existência.
    Retorna (bool, motivo).
    """
    try:
        answers = dns.resolver.resolve(domain, 'MX', lifetime=timeout)
        mx_hosts = [r.exchange.to_text() for r in answers]
        return True, ", ".join(mx_hosts)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        # Fallback para registros A/AAAA
        try:
            dns.resolver.resolve(domain, 'A', lifetime=timeout)
            return True, "A record"
        except Exception:
            try:
                dns.resolver.resolve(domain, 'AAAA', lifetime=timeout)
                return True, "AAAA record"
            except Exception:
                return False, "Domínio não encontrado"
    except Exception as e:
        return False, f"Erro DNS: {e}"

def processar_email(email, cache, lock):
    """
    Processa um email individualmente: valida sintaxe e domínio.
    Usa cache para evitar consultas DNS repetidas para o mesmo domínio.
    """
    email = email.strip()
    ok_syntax, normalized, reason = validar_sintaxe_email(email)
    if not ok_syntax:
        return (email, "Inválido", "Sintaxe inválida: " + reason)

    domain = normalized.split('@')[1].lower()
    # cache por domínio para evitar consultas repetidas
    with lock:
        cached = cache.get(domain)

    if cached is not None:
        mx_ok, mx_info = cached
    else:
        mx_ok, mx_info = validar_dominio_email(domain)
        with lock:
            cache[domain] = (mx_ok, mx_info)

    if mx_ok:
        return (normalized, "Válido", mx_info)
    else:
        return (normalized, "Inválido", mx_info)
    
def gerar_arquivo_csv(caminho_saida, dados):
    """
    Gera arquivo CSV com as colunas: email, status e motivo.
    """
    with open(caminho_saida, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['email', 'status', 'motivo'])
        for row in dados:
            writer.writerow(row)

def main(input_file='emails.txt', output_file='validacao_emails.csv', workers=10):
    # Leitura dos emails
    emails = ler_emails(input_file)
    logging.info(f"Carregados {len(emails)} e-mails de {input_file}")

    cache = {}
    lock = threading.Lock()
    results = []
    
    # Processamento paralelo dos emails para acelerar validação
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(processar_email, e, cache, lock): e for e in emails}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                logging.error("Erro processando: %s -> %s", futures[fut], e)
                results.append((futures[fut], "Inválido", f"Erro interno: {e}"))
                
    # Geração do CSV
    gerar_arquivo_csv(output_file, results)
    logging.info(f"Relatório gravado em: {output_file}")
    
    # Resumo final
    total = len(results)
    validos = sum(1 for r in results if r[1] == "Válido")
    invalidos = total - validos
    logging.info(f"Total: {total} | Válidos: {validos} | Inválidos: {invalidos}")

if __name__ == "__main__":
    infile = sys.argv[1] if len(sys.argv) > 1 else 'emails.txt'
    outfile = sys.argv[2] if len(sys.argv) > 2 else 'validacao_emails.csv'
    main(infile, outfile)
