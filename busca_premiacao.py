"""
Radar de Oportunidades
Lê o arquivo resultado_manual.json e envia o email formatado para a o responsavel.

Como usar toda semana:
1. Abra o Claude e cole o PROMPT_SEMANAL (salvo abaixo como referência)
2. Salve o JSON retornado como resultado_manual.json nesta pasta
3. Rode: python busca_premiacao.py
"""

import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import ssl
import os

# ============================================================
#  CONFIGURAÇÕES — edite apenas este bloco
# ============================================================

EMAIL_REMETENTE    = "gabriela.alcantara.queiroz@gmail.com"
EMAIL_SENHA        = "SUA_SENHA_DE_APP_AQUI"   # senha de app do Gmail
EMAIL_DESTINATARIO = "gabriela.alcantara.queiroz@gmail.com"
EMAIL_CC = "team@example.com"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# ============================================================
#  MAPEAMENTO DE ÍCONES E CORES
# ============================================================

CORES = {
    "alta":  ("#FCEBEB", "#A32D2D", "#E24B4A"),
    "media": ("#FAEEDA", "#854F0B", "#BA7517"),
    "baixa": ("#E1F5EE", "#0F6E56", "#1D9E75"),
}

ICONES_AREA = {
    "cultura":    "🎭",
    "esg":        "🌱",
    "diversidade":"🌈",
    "ong":        "🤝",
    "audiovisual":"🎬",
    "inovacao":   "💡",
    "patrimonio": "🏛️",
    "juventude":  "✊",
    "educacao":   "📚",
    "outro":      "🏆",
}

ICONES_TIPO = {
    "premiacao":       "🏆 Premiação",
    "edital":          "📋 Edital",
    "patrocinio":      "💼 Patrocínio",
    "chamada_publica": "📢 Chamada Pública",
    "programa":        "🔷 Programa",
    "reconhecimento":  "🎖️ Reconhecimento",
}

ICONES_PROMOTOR = {
    "governo":       "🏛️ Governo",
    "instituto":     "🏢 Instituto/Fundação",
    "banco":         "🏦 Banco/Empresa",
    "empresa":       "🏢 Empresa Privada",
    "internacional": "🌍 Internacional",
    "universidade":  "🎓 Universidade",
    "rede_cultural": "🕸️ Rede Cultural",
    "outro":         "🔷 Outro",
}

LABELS_URG = {
    "alta":  "Prazo urgente",
    "media": "Atenção",
    "baixa": "Monitorar",
}

# ============================================================
#  GERAÇÃO DO EMAIL HTML
# ============================================================

def gerar_email_html(resultado):
    data_busca = resultado.get("data_busca", datetime.now().strftime("%d/%m/%Y"))
    semana     = resultado.get("semana", "—")
    premiacoes = resultado.get("premiacoes", [])
    total      = len(premiacoes)

    grupos = {"alta": [], "media": [], "baixa": []}
    for p in premiacoes:
        grupos.setdefault(p.get("urgencia", "baixa"), []).append(p)

    def card(p):
        urg            = p.get("urgencia", "baixa")
        bg, txt, borda = CORES.get(urg, CORES["baixa"])
        label          = LABELS_URG.get(urg, "Monitorar")
        icone_area     = ICONES_AREA.get(p.get("area", "outro"), "🏆")
        tipo_label     = ICONES_TIPO.get(p.get("tipo", "outro"), "🔷 Oportunidade")
        promotor_label = ICONES_PROMOTOR.get(p.get("promotor", "outro"), "🔷 Outro")
        progs          = ", ".join(p.get("areas_impactadas", [])) or "Organização cultural geral"

        return f"""
        <div style="border-left:4px solid {borda};background:#ffffff;border-radius:8px;
                    padding:16px 18px;margin-bottom:14px;border:0.5px solid #e0e0e0;
                    border-left:4px solid {borda};">

          <div style="margin-bottom:10px;">
            <span style="font-size:18px;">{icone_area}</span>
            <span style="font-size:15px;font-weight:600;color:#1a1a1a;margin-left:6px;">{p.get('nome','—')}</span>
            <span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:99px;
                         background:{bg};color:{txt};margin-left:8px;">{label}</span>
          </div>

          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
            <span style="font-size:11px;color:#777;background:#f5f5f3;padding:2px 8px;
                         border-radius:4px;border:0.5px solid #e0e0e0;">{tipo_label}</span>
            <span style="font-size:11px;color:#777;background:#f5f5f3;padding:2px 8px;
                         border-radius:4px;border:0.5px solid #e0e0e0;">{promotor_label}</span>
          </div>

          <p style="margin:0 0 4px;font-size:13px;color:#555;">
            <strong>Organizador:</strong> {p.get('organizador','—')}
          </p>
          <p style="margin:0 0 4px;font-size:13px;color:#555;">
            <strong>Prazo:</strong> {p.get('prazo','Verificar no link')}
          </p>
          <p style="margin:0 0 4px;font-size:13px;color:#555;">
            <strong>Áreas de Impacto:</strong> {progs}
          </p>
          <p style="margin:8px 0 14px;font-size:13px;color:#444;font-style:italic;
                    border-left:2px solid #e0e0e0;padding-left:10px;">
            {p.get('por_que_participar','')}
          </p>

          <a href="{p.get('link','#')}"
             style="display:inline-block;background:#1a1a1a;color:#ffffff;font-size:12px;
                    font-weight:600;padding:7px 16px;border-radius:6px;text-decoration:none;">
            Ver oportunidade →
          </a>
        </div>"""

    secoes  = ""
    titulos = {
        "alta":  "🔴 Prazo urgente — ação imediata",
        "media": "🟡 Atenção — prazo chegando",
        "baixa": "🟢 Monitorar — abre em breve",
    }
    for urg in ["alta", "media", "baixa"]:
        if grupos.get(urg):
            secoes += f"""
            <h2 style="font-size:14px;font-weight:600;color:#333;margin:24px 0 10px;
                        border-bottom:1px solid #eee;padding-bottom:6px;">{titulos[urg]}</h2>
            {"".join(card(p) for p in grupos[urg])}"""

    # Resumo por tipo
    tipos_count = {}
    for p in premiacoes:
        t = ICONES_TIPO.get(p.get("tipo", "outro"), "🔷 Oportunidade")
        tipos_count[t] = tipos_count.get(t, 0) + 1
    resumo = " &nbsp;·&nbsp; ".join(
        f"<strong>{v}</strong> {k}" for k, v in tipos_count.items()
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f5f3;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f3;padding:24px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;overflow:hidden;
                    border:0.5px solid #e0ddd6;max-width:600px;width:100%;">

        <tr><td style="background:#1a1a1a;padding:24px 28px;">
          <p style="margin:0;font-size:11px;color:#888;letter-spacing:0.08em;text-transform:uppercase;">
            Prospecção Estratégica · Semana {semana} · {data_busca}
          </p>
          <h1 style="margin:6px 0 0;font-size:22px;font-weight:700;color:#ffffff;">
            Radar de Oportunidades
          </h1>
          <p style="margin:6px 0 0;font-size:13px;color:#aaa;">
            {total} nova{"s" if total != 1 else ""} oportunidade{"s" if total != 1 else ""} mapeada{"s" if total != 1 else ""} esta semana
          </p>
        </td></tr>

        <tr><td style="background:#f9f8f6;padding:12px 28px;border-bottom:0.5px solid #e8e5e0;">
          <p style="margin:0;font-size:12px;color:#888;">{resumo}</p>
        </td></tr>

        <tr><td style="padding:24px 28px;">
          {secoes}
          <div style="margin-top:32px;padding-top:16px;border-top:1px solid #eee;
                      font-size:11px;color:#aaa;text-align:center;">
           Radar de Oportunidades · {data_busca}<br>
            Prospecção estratégica com busca real na web · Claude Pro
          </div>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

# ============================================================
#  ENVIO DO EMAIL
# ============================================================

def enviar_email(html, total, semana):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Organização] Radar de Oportunidades — Semana {semana} ({total} nova{'s' if total != 1 else ''})"
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINATARIO
    if EMAIL_CC:
        msg["Cc"] = EMAIL_CC

    msg.attach(MIMEText(html, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ctx)
        smtp.login(EMAIL_REMETENTE, EMAIL_SENHA)
        destinatarios = [EMAIL_DESTINATARIO] + ([EMAIL_CC] if EMAIL_CC else [])
        smtp.sendmail(EMAIL_REMETENTE, destinatarios, msg.as_string())

# ============================================================
#  EXECUÇÃO PRINCIPAL
# ============================================================

if __name__ == "__main__":
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Iniciando envio do Radar de Oportunidades...")

    json_path = os.path.join(os.path.dirname(__file__), "resultado_manual.json")

    if not os.path.exists(json_path):
        print(f"  [ERRO] Arquivo não encontrado: {json_path}")
        print("  Peça ao Claude a busca semanal e salve o JSON como resultado_manual.json")
        raise SystemExit(1)

    with open(json_path, encoding="utf-8") as f:
        resultado = json.load(f)

    premiacoes = resultado.get("premiacoes", [])
    total      = len(premiacoes)
    semana     = resultado.get("semana", "—")

    print(f"  → {total} oportunidades carregadas do JSON")

    if total == 0:
        print("  → Nenhuma oportunidade no JSON. Encerrando.")
        raise SystemExit(0)

    html = gerar_email_html(resultado)
    enviar_email(html, total, semana)

    print(f"  → Email enviado para {EMAIL_DESTINATARIO}")
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Concluído!")
