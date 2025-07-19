# app/utils/status_calculator.py
import re
from datetime import datetime, date, timedelta
import pandas as pd

# --- Carrega a lista de feriados em um set de date() ---
FERIADOS_FILE = r"\\pfl-cps-file\Divisao_GD\Feriados.txt"
holidays = set()
try:
    with open(FERIADOS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # pula cabeçalho ou linhas em branco
            if not line or line.lower().startswith("data"):
                continue
            try:
                # formata: "DD/MM/YYYY"
                d = datetime.strptime(line, "%d/%m/%Y").date()
                holidays.add(d)
            except ValueError:
                # ignora linhas mal formatadas
                continue
except Exception:
    # se der erro ao ler (arquivo não existe, permissão etc), segue sem feriados
    holidays = set()
    
    
def calcular_tipo_projeto(data_parecer, data_cadastro, cd_status):
    try:
        d1 = pd.to_datetime(data_parecer, dayfirst=True).normalize()
        d2 = pd.to_datetime(data_cadastro, dayfirst=True).normalize()
        if d1 == d2:
            return "Novo Projeto"
        if d1 != d2 and cd_status == 224:
            return "No Inbox"
        if d1 != d2 and cd_status != 224:
            return "Reanálise"
    except Exception:
        pass
    return "Indefinido"


def calcular_status(data_prazo_str: str) -> str:
    """
    Converte uma string de data em D0, D1… D7+ ou '' se inválido.
    Suporta três formatos:
      - 'YYYY-MM-DD'      (ex: '2025-04-25')
      - 'DD-MM-YY'        (ex: '12-04-23')
      - 'DD-MM-YYYY'      (ex: '12-04-2023')
    Se a string não corresponder a nenhum, retorna ''.
    """
    if not data_prazo_str or not isinstance(data_prazo_str, str):
        return ""

    s = data_prazo_str.strip()

    # Detecta o formato pelo pattern
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        fmt = "%Y-%m-%d"
    elif re.fullmatch(r"\d{2}-\d{2}-\d{2}", s):
        fmt = "%d-%m-%y"
    elif re.fullmatch(r"\d{2}-\d{2}-\d{4}", s):
        fmt = "%d-%m-%Y"
    else:
        return ""

    # Faz o parse
    try:
        data_prazo = datetime.strptime(s, fmt).date()
    except ValueError:
        return ""

    hoje = date.today()
    if data_prazo > hoje:
        return ""  # prazo no futuro

    # Conta só dias úteis entre (data_prazo, hoje], excluindo sábados/domingos e feriados
    cont = 0
    atual = data_prazo
    while atual < hoje:
        atual += timedelta(days=1)
        if atual.weekday() < 5 and atual not in holidays:
            cont += 1
            if cont > 7:
                return "D7+"

    return f"D{cont}"
