# app/utils/email_sender.py

import json
import requests
from app.config.settings import (
    POWER_AUTOMATE_URL,
    REMETENTE_FIXO,
    API_KEY
)
from datetime import datetime, timedelta

def build_email_html(
    report_text: str,
    with_deadline: bool,
    deadline_days: int
) -> str:
    """
    Monta o corpo do e-mail em HTML a partir do texto puro do parecer,
    incluindo ou não o prazo de acordo com with_deadline.
    """
    html_parts = []

    # 1) Header: days + end date
    if with_deadline:
        end_date = (datetime.now() + timedelta(days=deadline_days)).strftime("%d/%m/%Y")
        plural = "s" if deadline_days > 1 else ""
        html_parts.append(
            f"<p><strong>Prazo:</strong> {deadline_days} dia{plural} (até {end_date})</p>"
        )

    # 2) Greeting (only once)
    html_parts.append("<p>Prezado(a) Cliente,</p>")

    # 3) Parse the raw report_text
    lines = [l.strip() for l in report_text.splitlines() if l.strip()]
    pendencias = []
    intro_lines = []

    for line in lines:
        # skip duplicate greeting
        if line.lower().startswith("prezado"):
            continue

        # collect flags/pendências
        if line.startswith("- "):
            pendencias.append(line[2:])

        # group headers like "Documentação:"
        elif line.endswith(":") and not line.lower().startswith("após"):
            html_parts.append(f"<p>{line}</p>")

        # the two closing instructions
        elif line.lower().startswith("solicitamos que") or line.lower().startswith("após realizar"):
            if with_deadline:
                html_parts.append(f"<p>{line}</p>")

        # everything else goes into the single intro paragraph
        else:
            intro_lines.append(line)

    # 4) The intro paragraph
    if intro_lines:
        html_parts.append(f"<p>{' '.join(intro_lines)}</p>")

    # 5) Pendências as a bullet list
    if pendencias:
        html_parts.append("<ul>")
        for p in pendencias:
            html_parts.append(f"  <li>{p}</li>")
        html_parts.append("</ul>")

    # 6) Signature
    html_parts.append(
        "<p>Atenciosamente,<br>Equipe de Análise de Projetos – CPFL</p>"
    )

    return "\n".join(html_parts)


def enviar_email_power_automate_html(
    destinatario: str,
    assunto: str,
    html_body: str
) -> bool:
    """
    Dispara o e-mail via Power Automate, enviando HTML no corpo.
    """
    payload = {
        "remetente": REMETENTE_FIXO,
        "destinatario": destinatario,
        "assunto": assunto,
        "corpo": html_body,
        "apiKey": API_KEY
    }
    headers = {"Content-Type": "application/json; charset=utf-8"}

    resp = requests.post(POWER_AUTOMATE_URL, headers=headers, data=json.dumps(payload))
    return resp.status_code in (200, 202)
