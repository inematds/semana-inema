#!/usr/bin/env python3
"""semana.py — a semana sem sobrecarga: o post semanal da sua comunidade.

Lê as fontes da semana (tabela markdown de produções, git log de repos, feed local),
as vitórias e os ajudantes, e monta a edição em 3 saídas:
  saida/<aaaa-mm-dd>/telegram.md   (cabe numa mensagem; se passar de 4.096, vira telegram-2.md, -3…)
  saida/<aaaa-mm-dd>/email.html    (e-mail simples)
  saida/<aaaa-mm-dd>/pagina.html   (página bonita, celular sem rolagem lateral)

Não publica nada: só gera arquivos. Quem cola/publica é o moderador.
Só biblioteca padrão. Sem rede.

Uso:
  python3 semana.py rascunho [--ate AAAA-MM-DD] [--de AAAA-MM-DD] [--dias 7]
  python3 semana.py gerar    [--ate AAAA-MM-DD] [--de AAAA-MM-DD] [--dias 7] [--edicao edicao.md]
Opções comuns: --config config.json  --saida saida  --vitorias X.md  --ajudantes X.md
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

LIMITE_TELEGRAM = 4096
URL_RE = re.compile(r"https?://[^\s<>\]\)\"'`|]+")


# ---------------------------------------------------------------- utilidades

def u16(texto):
    """Tamanho como o Telegram conta (unidades UTF-16; emoji vale 2)."""
    return len(texto.encode("utf-16-le")) // 2


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def chave(s):
    return re.sub(r"[^a-z0-9 ]", "", sem_acento(s).lower()).strip()


def limpa_md(s):
    """Tira negrito, crase e link markdown de uma célula."""
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", s)
    s = s.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def primeira_url(s):
    m = URL_RE.search(s or "")
    return m.group(0).rstrip(".,;:") if m else ""


def corta(s, n):
    """Corta em até n caracteres, na última palavra inteira, com reticências."""
    s = s.strip()
    if len(s) <= n:
        return s
    t = s[: n - 1]
    if " " in t[n // 2:]:
        t = t[: t.rindex(" ")]
    return t.rstrip(" ,;:—-") + "…"


def caminho(base, p):
    p = os.path.expanduser(str(p))
    return Path(p) if os.path.isabs(p) else (Path(base) / p)


def data_br(d):
    return d.strftime("%d/%m")


# ---------------------------------------------------------------- janela

def janela(ate, dias=7, de=None):
    """Janela fechada [de, ate]. Padrão: os 7 dias que terminam em `ate` (ate-6 … ate)."""
    if de is None:
        de = ate - dt.timedelta(days=dias - 1)
    if de > ate:
        raise ValueError("--de depois de --ate")
    return de, ate


def na_janela(d, jan):
    return d is not None and jan[0] <= d <= jan[1]


# ---------------------------------------------------------------- fonte: tabela markdown

DATA_COMPLETA = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def titulo_curto(tema, curto=25, maximo=90):
    """Título para o post: a parte antes do 1º ' — ' ou ' ('. Se essa parte for curta (só um nome,
    como 'MovieFlow'), junta o começo da explicação: 'MovieFlow — filme de IA de graça'.
    Devolve (titulo, detalhe)."""
    m = re.search(r" — | \(", tema)
    if not m:
        return corta(tema, maximo), ""
    cabeca, resto = tema[: m.start()].strip(), tema[m.end():].strip(" )")
    if len(cabeca) < curto and m.group(0) == " — " and resto:
        trecho = re.split(r" \(| \+ |; |: ", resto, maxsplit=1)[0]
        if len(trecho) < 12:
            trecho = corta(re.split(r" \(", resto, maxsplit=1)[0], 60)
        return corta(f"{cabeca} — {trecho}", maximo), resto
    return corta(cabeca, maximo), resto


def _celulas(linha):
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def _monta_data(dia, mes, ano):
    try:
        return dt.date(int(ano), int(mes), int(dia))
    except ValueError:
        return None


def ler_tabela_md(texto, fonte):
    """Lê uma tabela markdown de produções. Devolve (itens, contagem).

    Regras:
    - só vale a tabela que tem a coluna `coluna_titulo` no cabeçalho; linhas acima dele são ignoradas;
    - só entra linha cuja 1ª parte do estado (antes de " — ", ":" ou ";") tem a palavra de `so_com`
      (INEMA: "publicad", que casa publicado/publicada; em inglês, use "published");
    - data = a data escrita depois dessa palavra (dd/mm ou dd/mm/aaaa); se não houver, a data da coluna_data;
      ano que falta vem da coluna_data; sem data nenhuma → contada como "sem data" e fica de fora.
    """
    col_t = chave(fonte.get("coluna_titulo", "Tema"))
    col_d = chave(fonte.get("coluna_data", "Dono"))
    col_e = chave(fonte.get("coluna_estado", "Estado"))
    exige = sem_acento(fonte.get("so_com", "publicad")).lower()
    linhas = texto.splitlines()
    cont = {"linhas": 0, "acima_do_cabecalho": 0, "nao_publicadas": 0, "sem_data": 0, "publicadas": 0}
    itens = []
    idx = None
    i = 0
    while i < len(linhas):
        ln = linhas[i]
        if ln.lstrip().startswith("|"):
            cel = [chave(c) for c in _celulas(ln)]
            prox = linhas[i + 1] if i + 1 < len(linhas) else ""
            if any(c.startswith(col_t) for c in cel) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", prox):
                idx = {
                    "t": next(k for k, c in enumerate(cel) if c.startswith(col_t)),
                    "d": next((k for k, c in enumerate(cel) if c.startswith(col_d)), None),
                    "e": next((k for k, c in enumerate(cel) if c.startswith(col_e)), None),
                }
                i += 2
                continue
            if idx is None:
                cont["acima_do_cabecalho"] += 1
                i += 1
                continue
            cont["linhas"] += 1
            c = _celulas(ln)
            pega = lambda k: c[k] if k is not None and k < len(c) else ""
            tema, dono, estado = pega(idx["t"]), pega(idx["d"]), pega(idx["e"])
            est_limpo = estado.replace("**", "").strip()
            cabeca = re.split(r" — |: |; ", est_limpo, maxsplit=1)[0]
            if exige not in sem_acento(cabeca).lower():
                cont["nao_publicadas"] += 1
                i += 1
                continue
            md = DATA_COMPLETA.search(dono)
            ano_dono = md.group(3) if md else None
            d = None
            mp = re.search(re.escape(exige) + r"\w*[^0-9]{0,25}?(\d{1,2})/(\d{1,2})(?:/(\d{4}))?",
                           sem_acento(est_limpo), re.I)
            if mp:
                ano = mp.group(3) or ano_dono
                if ano:
                    d = _monta_data(mp.group(1), mp.group(2), ano)
            if d is None and md:
                d = _monta_data(md.group(1), md.group(2), md.group(3))
            if d is None:
                cont["sem_data"] += 1
                i += 1
                continue
            cont["publicadas"] += 1
            tema_l = limpa_md(tema)
            titulo, detalhe = titulo_curto(tema_l)
            link = primeira_url(estado)
            if not link and fonte.get("padrao_id_youtube"):
                my = re.search(fonte["padrao_id_youtube"], estado)
                if my:
                    link = "https://www.youtube.com/watch?v=" + my.group(1)
            itens.append({
                "data": d,
                "titulo": titulo,
                "detalhe": detalhe,
                "link": link,
                "fonte": fonte.get("nome", "tabela"),
            })
        else:
            if idx is not None and ln.strip() == "":
                pass
        i += 1
    return itens, cont


# ---------------------------------------------------------------- fonte: git log

def ler_git_log(fonte, jan, base):
    itens = []
    ignorar = [p.lower() for p in fonte.get("ignorar_prefixos", [])]
    for repo in fonte.get("repos", []):
        rp = caminho(base, repo)
        if not (rp / ".git").exists():
            print(f"  aviso: {rp} não é repositório git — pulei", file=sys.stderr)
            continue
        cmd = ["git", "-C", str(rp), "log", "--no-merges", "--date=short",
               f"--since={jan[0].isoformat()} 00:00:00", f"--until={jan[1].isoformat()} 23:59:59",
               "--pretty=format:%ad%x09%s"]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        for ln in out.splitlines():
            if "\t" not in ln:
                continue
            ds, assunto = ln.split("\t", 1)
            if any(assunto.lower().startswith(p) for p in ignorar):
                continue
            try:
                d = dt.date.fromisoformat(ds)
            except ValueError:
                continue
            if na_janela(d, jan):
                itens.append({"data": d, "titulo": f"{rp.name}: {assunto.strip()}", "detalhe": "",
                              "link": fonte.get("link_repo", {}).get(rp.name, ""),
                              "fonte": fonte.get("nome", "git")})
    return itens


# ---------------------------------------------------------------- fonte: feed local (JSON ou RSS/Atom)

def _data_qualquer(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(s).date()
    except (TypeError, ValueError):
        pass
    m = DATA_COMPLETA.search(s)
    return _monta_data(*m.groups()) if m else None


def ler_feed(fonte, jan, base):
    p = str(fonte.get("caminho", ""))
    if p.startswith("http"):
        print("  aviso: feed por URL não é lido (o kit não usa rede). Salve o arquivo e aponte o caminho.",
              file=sys.stderr)
        return []
    arq = caminho(base, p)
    if not arq.exists():
        print(f"  aviso: feed {arq} não existe — pulei", file=sys.stderr)
        return []
    brutos = []
    if arq.suffix.lower() == ".json":
        dados = json.loads(arq.read_text(encoding="utf-8"))
        if isinstance(dados, dict):
            dados = dados.get("items") or dados.get("itens") or []
        for it in dados:
            brutos.append((it.get("titulo") or it.get("title") or "",
                           it.get("data") or it.get("date") or it.get("date_published") or "",
                           it.get("link") or it.get("url") or ""))
    else:
        raiz = ET.parse(arq).getroot()
        for it in raiz.iter():
            tag = it.tag.split("}")[-1]
            if tag not in ("item", "entry"):
                continue
            achar = lambda nome: next((f for f in it if f.tag.split("}")[-1] == nome), None)
            t = achar("title")
            d = achar("pubDate") or achar("published") or achar("updated")
            l = achar("link")
            link = (l.get("href") or l.text or "") if l is not None else ""
            brutos.append((t.text if t is not None else "", d.text if d is not None else "", link))
    itens = []
    for titulo, ds, link in brutos:
        d = _data_qualquer(ds)
        if titulo and na_janela(d, jan):
            itens.append({"data": d, "titulo": limpa_md(titulo), "detalhe": "", "link": link.strip(),
                          "fonte": fonte.get("nome", "feed")})
    return itens


# ---------------------------------------------------------------- juntar fontes

def coletar(cfg, base, jan):
    todos, resumo = [], []
    for f in cfg.get("fontes", []):
        if not f.get("ativo", True):
            continue
        tipo = f.get("tipo")
        if tipo == "tabela_md":
            arq = caminho(base, f["caminho"])
            if not arq.exists():
                print(f"  aviso: tabela {arq} não existe — pulei", file=sys.stderr)
                resumo.append((f.get("nome", "tabela"), {"ARQUIVO_NAO_ENCONTRADO": str(arq)}))
                continue
            itens, cont = ler_tabela_md(arq.read_text(encoding="utf-8"), f)
            dentro = [x for x in itens if na_janela(x["data"], jan)]
            cont["na_janela"] = len(dentro)
            resumo.append((f.get("nome", "tabela"), cont))
            todos += dentro
        elif tipo == "git_log":
            itens = ler_git_log(f, jan, base)
            resumo.append((f.get("nome", "git"), {"na_janela": len(itens)}))
            todos += itens
        elif tipo == "feed":
            itens = ler_feed(f, jan, base)
            resumo.append((f.get("nome", "feed"), {"na_janela": len(itens)}))
            todos += itens
        else:
            print(f"  aviso: tipo de fonte desconhecido: {tipo}", file=sys.stderr)
    todos.sort(key=lambda x: (x["data"], x["titulo"]), reverse=True)
    return todos, resumo


# ---------------------------------------------------------------- vitórias, ajudantes, edição

def _linhas_lista(texto):
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    for ln in texto.splitlines():
        ln = ln.strip()
        if ln.startswith(("- ", "* ")):
            yield ln[2:].strip()


def ler_vitorias(texto):
    """`- Nome — o que fez — link` (o link é opcional)."""
    out = []
    for ln in _linhas_lista(texto):
        partes = [p.strip() for p in re.split(r" — | \| ", ln)]
        link = primeira_url(ln)
        partes = [p for p in partes if p and not URL_RE.fullmatch(p.rstrip(".,;"))]
        if not partes:
            continue
        out.append({"nome": limpa_md(partes[0]), "feito": limpa_md(" — ".join(partes[1:])), "link": link})
    return out


def ler_ajudantes(texto):
    """`- Nome — 12 respostas — observação`. Ordena pelo 1º número, do maior para o menor."""
    out = []
    for ln in _linhas_lista(texto):
        partes = [p.strip() for p in ln.split(" — ")]
        m = re.search(r"\d+", " ".join(partes[1:]))
        out.append({"nome": limpa_md(partes[0]), "pontos": int(m.group(0)) if m else 0,
                    "nota": limpa_md(" — ".join(partes[1:]))})
    return sorted(out, key=lambda x: -x["pontos"])


# Nomes aceitos no edicao.md (PT, EN, ES), para o guia traduzido funcionar igual.
SECOES_EDICAO = {
    "unica": ("a unica coisa", "the one thing", "lo unico"),
    "caso": ("seu caso", "your case", "tu caso"),
    "ignorar": ("pode ignorar", "you can ignore", "puedes ignorar"),
    "travou": ("travou", "stuck", "te trabaste"),
    "abertura": ("abertura", "opening", "apertura"),
}
CHAVES_UNICA = {"title": "titulo", "why": "porque", "result": "resultado", "time": "tempo", "tiempo": "tempo",
                "week": "semana", "enlace": "link"}


def ler_edicao(texto):
    """Lê o edicao.md preenchido (moderador ou agente). Seções por `## `."""
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    secoes, atual = {}, None
    for ln in texto.splitlines():
        if ln.startswith("## "):
            atual = chave(ln[3:])
            secoes[atual] = []
        elif atual is not None:
            secoes[atual].append(ln)

    def acha(nome):
        nomes = SECOES_EDICAO[nome]
        return next((v for k, v in secoes.items() if k.startswith(nomes)), [])

    unica = {}
    for ln in acha("unica"):
        m = re.match(r"^\s*[-*]?\s*([^:]{2,20}):\s*(.+)$", ln)
        if m:
            k = chave(m.group(1)).replace(" ", "")
            unica[CHAVES_UNICA.get(k, k)] = m.group(2).strip()
    caso = []
    for ln in acha("caso"):
        if ln.strip().startswith("|") and not re.match(r"^\s*\|[\s:\-|]+\|\s*$", ln):
            c = _celulas(ln)
            if len(c) >= 2 and chave(c[0]) not in ("voce usa", "seu caso", "your case", "tu caso", "you use", "usas"):
                caso.append({"usa": limpa_md(c[0]), "veja": limpa_md(c[1]), "link": primeira_url(c[1])})
    ignorar = list(_linhas_lista("\n".join(acha("ignorar"))))
    travou = "\n".join(acha("travou")).strip()
    abertura = "\n".join(acha("abertura")).strip()
    return {
        "unica": {
            "titulo": unica.get("titulo", ""),
            "porque": unica.get("porque", ""),
            "resultado": unica.get("resultado", ""),
            "tempo": unica.get("tempo", ""),
            "link": primeira_url(unica.get("link", "")),
            "semana": unica.get("semana", "").strip(),
        },
        "caso": caso,
        "ignorar": [limpa_md(x) for x in ignorar],
        "travou": limpa_md(travou),
        "abertura": limpa_md(abertura),
    }


# ---------------------------------------------------------------- Telegram

CABECALHO_SECAO = re.compile(r"^\d\) ")


def dividir(texto, limite=LIMITE_TELEGRAM):
    """Divide o texto em partes de até `limite` unidades UTF-16.
    Corta de preferência no início de uma seção ("3) …"), depois em fim de linha, e só em último caso
    no meio da linha. ''.join(partes) == texto."""
    if u16(texto) <= limite:
        return [texto]
    linhas = texto.splitlines(keepends=True)
    blocos, atual = [], []
    for ln in linhas:
        if CABECALHO_SECAO.match(ln) and atual:
            blocos.append("".join(atual))
            atual = []
        atual.append(ln)
    if atual:
        blocos.append("".join(atual))

    pedacos = []
    for b in blocos:
        if u16(b) <= limite:
            pedacos.append(b)
            continue
        for ln in b.splitlines(keepends=True):
            while u16(ln) > limite:
                corte = limite
                while u16(ln[:corte]) > limite:
                    corte -= 1
                pedacos.append(ln[:corte])
                ln = ln[corte:]
            pedacos.append(ln)

    partes, cur = [], ""
    for p in pedacos:
        if cur and u16(cur) + u16(p) > limite:
            partes.append(cur)
            cur = ""
        cur += p
    if cur:
        partes.append(cur)
    return partes


def texto_telegram(ed, cfg, jan, chegou, vitorias, ajudantes):
    nome = cfg.get("comunidade", "Comunidade")
    L = []
    L.append(f"{cfg.get('titulo_post', 'A SEMANA SEM SOBRECARGA')} · {nome}")
    L.append(f"De {data_br(jan[0])} a {data_br(jan[1])}/{jan[1].year}")
    L.append(ed["abertura"] or "Uma coisa só para fazer. O resto pode esperar.")
    L.append("")
    u = ed["unica"]
    L.append("1) A ÚNICA COISA DESTA SEMANA")
    L.append(u["titulo"])
    if u["porque"]:
        L.append(f"Por quê: {u['porque']}")
    if u["resultado"]:
        L.append(f"Pronto quando: {u['resultado']}")
    if u["tempo"]:
        L.append(f"Tempo: {u['tempo']}")
    if u["link"]:
        L.append(f"Comece aqui: {u['link']}")
    L.append("")
    L.append("2) SEU CASO → SEU CAMINHO")
    for c in ed["caso"]:
        L.append(f"• {c['usa']} → {c['veja']}" + (f" {c['link']}" if c["link"] and c["link"] not in c["veja"] else ""))
    if not ed["caso"]:
        L.append("• (sem tabela nesta edição)")
    L.append("")
    L.append("3) VITÓRIAS DA COMUNIDADE")
    for v in vitorias:
        L.append(f"• {v['nome']} — {v['feito']}" + (f" {v['link']}" if v["link"] else ""))
    if not vitorias:
        L.append(f"• Ainda sem vitórias nesta edição. Fez algo funcionar? Conte no grupo: {cfg.get('link', '')}")
    L.append("")
    mx = int(cfg.get("max_o_que_chegou_telegram", 12))
    L.append(f"4) O QUE CHEGOU ({len(chegou)} na semana)")
    for it in chegou[:mx]:
        L.append(f"• {data_br(it['data'])} {corta(it['titulo'], 70)}" + (f" {it['link']}" if it["link"] else ""))
    if len(chegou) > mx:
        L.append(f"• e mais {len(chegou) - mx} na página da semana.")
    if not chegou:
        L.append("• Nada novo nas fontes nesta semana.")
    L.append("")
    L.append("5) PODE IGNORAR")
    for x in ed["ignorar"] or ["(nada nesta semana)"]:
        L.append(f"• {x}")
    L.append("")
    pl = cfg.get("plantao", {})
    L.append("6) TRAVOU?")
    L.append(ed["travou"] or pl.get("texto", "Pergunte no grupo com o print do erro."))
    if pl.get("link"):
        L.append(pl["link"])
    L.append("")
    L.append("7) QUEM MAIS AJUDOU")
    if ajudantes:
        for k, a in enumerate(ajudantes[:5], 1):
            L.append(f"{k}. {a['nome']} — {a['nota']}")
    else:
        L.append(cfg.get("ajudantes_vazio", "Ranking desta semana ainda vazio: anote em ajudantes.md quem respondeu dúvidas no grupo."))
    L.append("")
    L.append(f"{nome} · {cfg.get('link', '')}")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- HTML (página e e-mail)

def e(s):
    return html.escape(s or "", quote=True)


def a(link, texto=None):
    if not link or not link.startswith(("http://", "https://")):
        return e(texto or "")
    return f'<a href="{e(link)}" target="_blank" rel="noopener">{e(texto or link)}</a>'


PAGINA_CSS = """
:root{--bg:#0c0c10;--bg2:#14141b;--card:#16161e;--line:#272730;--txt:#e9e9ee;--mut:#9a9aa6;--amb:#FACC15;--amb-ink:#1a1206;--sky:#38bdf8;--ok:#7CE0C6}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f6f7f9;--bg2:#eceef2;--card:#ffffff;--line:#e1e3ea;--txt:#1a1a22;--mut:#5b5b68;--amb:#a16207;--sky:#0369a1;--ok:#0E6B55}}
:root[data-theme="light"]{--bg:#f6f7f9;--bg2:#eceef2;--card:#ffffff;--line:#e1e3ea;--txt:#1a1a22;--mut:#5b5b68;--amb:#a16207;--sky:#0369a1;--ok:#0E6B55}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--txt);font:16px/1.65 Inter,system-ui,sans-serif}
a{color:var(--amb);overflow-wrap:anywhere}
.wrap{max-width:860px;margin:0 auto;padding:28px 16px 64px}
header .chip{font:600 .75rem Sora,Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--amb)}
h1{font:800 clamp(30px,6vw,48px)/1.08 Sora,Inter,sans-serif;letter-spacing:-.02em;margin:.25em 0 .3em}
h2{font:700 1.2rem/1.3 Sora,Inter,sans-serif;margin:0 0 .7em;display:flex;gap:.6em;align-items:center}
h2 .n{display:inline-flex;min-width:30px;height:30px;align-items:center;justify-content:center;border-radius:12px;background:var(--amb);color:var(--amb-ink);font-size:.9rem;flex:0 0 auto}
.lead{color:var(--mut);margin:0 0 6px;max-width:68ch}
.meta{color:var(--mut);font-size:.9rem}
section{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 18px;margin:16px 0}
section.unica{border:2px solid var(--amb);padding:24px 20px}
.unica .titulo{font:800 clamp(22px,4.4vw,30px)/1.2 Sora,Inter,sans-serif;margin:.1em 0 .5em}
.unica dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:6px 14px}
.unica dt{color:var(--mut);font-weight:600}.unica dd{margin:0}
.btn{display:inline-block;margin-top:14px;background:var(--amb);color:var(--amb-ink);font:600 1rem Sora,Inter,sans-serif;padding:.65em 1.1em;border-radius:10px;text-decoration:none}
ul{margin:0;padding-left:1.1em}li{margin:.35em 0}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px 8px;border-top:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:600;font-size:.85rem;text-transform:uppercase;letter-spacing:.06em;border-top:0}
.data{color:var(--mut);font:500 .85rem 'JetBrains Mono',monospace;white-space:nowrap;margin-right:.4em}
.det{color:var(--mut);font-size:.92rem}
.vazio{color:var(--mut)}
.rank{counter-reset:r;list-style:none;padding:0}.rank li{counter-increment:r}.rank li::before{content:counter(r) "º ";color:var(--amb);font-weight:700}
footer{color:var(--mut);font-size:.9rem;margin-top:28px;text-align:center}
footer a{color:var(--sky)}
@media (max-width:560px){
 .unica dl{grid-template-columns:1fr}.unica dd{margin-bottom:6px}
 table thead{display:none}table,tbody,tr,td{display:block;width:100%}
 tr{border-top:1px solid var(--line);padding:8px 0}td{border:0;padding:2px 0}
 td:first-child{font-weight:600}
}
"""


def html_pagina(ed, cfg, jan, chegou, vitorias, ajudantes):
    nome = cfg.get("comunidade", "Comunidade")
    u = ed["unica"]
    pl = cfg.get("plantao", {})
    S = []
    S.append(f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Semana {e(nome)} · {data_br(jan[0])} a {data_br(jan[1])}</title>
<meta name="description" content="A única coisa desta semana, as vitórias e o que pode ignorar.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&family=Sora:wght@600;700;800&display=swap" rel="stylesheet">
<style>{PAGINA_CSS}</style></head><body><div class="wrap">
<header><span class="chip">{e(nome)} · de {data_br(jan[0])} a {data_br(jan[1])}/{jan[1].year}</span>
<h1>{e(cfg.get('titulo_pagina', 'A semana sem sobrecarga'))}</h1>
<p class="lead">{e(ed['abertura'] or 'Uma coisa só para fazer. O resto pode esperar.')}</p></header>""")
    det = []
    if u["porque"]:
        det.append(f"<dt>Por quê</dt><dd>{e(u['porque'])}</dd>")
    if u["resultado"]:
        det.append(f"<dt>Pronto quando</dt><dd>{e(u['resultado'])}</dd>")
    if u["tempo"]:
        det.append(f"<dt>Tempo</dt><dd>{e(u['tempo'])}</dd>")
    btn = f'<a class="btn" href="{e(u["link"])}" target="_blank" rel="noopener">Comece aqui</a>' if u["link"] else ""
    S.append(f"""<section class="unica" id="unica"><h2><span class="n">1</span>A única coisa desta semana</h2>
<p class="titulo">{e(u['titulo'])}</p><dl>{''.join(det)}</dl>{btn}</section>""")
    linhas = "".join(f"<tr><td>{e(c['usa'])}</td><td>{a(c['link'], c['veja']) if c['link'] else e(c['veja'])}</td></tr>"
                     for c in ed["caso"])
    S.append(f"""<section id="caso"><h2><span class="n">2</span>Seu caso → seu caminho</h2>
{'<table><thead><tr><th>Seu caso</th><th>Veja</th></tr></thead><tbody>' + linhas + '</tbody></table>' if linhas else '<p class="vazio">Sem tabela nesta edição.</p>'}</section>""")
    vit = "".join(f"<li><strong>{e(v['nome'])}</strong> — {e(v['feito'])}" + (f" · {a(v['link'], 'ver')}" if v["link"] else "") + "</li>"
                  for v in vitorias)
    S.append(f"""<section id="vitorias"><h2><span class="n">3</span>Vitórias da comunidade</h2>
{'<ul>' + vit + '</ul>' if vit else '<p class="vazio">Ainda sem vitórias nesta edição. Fez algo funcionar? Conte no grupo.</p>'}</section>""")
    ch = "".join(f"<li><span class=\"data\">{data_br(it['data'])}</span>{a(it['link'], it['titulo']) if it['link'] else e(it['titulo'])}"
                 + (f"<br><span class=\"det\">{e(corta(it['detalhe'], 160))}</span>" if it["detalhe"] and cfg.get("mostrar_detalhe") else "") + "</li>"
                 for it in chegou)
    S.append(f"""<section id="chegou"><h2><span class="n">4</span>O que chegou <span class="meta">({len(chegou)} na semana)</span></h2>
{'<ul>' + ch + '</ul>' if ch else '<p class="vazio">Nada novo nas fontes nesta semana.</p>'}</section>""")
    ig = "".join(f"<li>{e(x)}</li>" for x in ed["ignorar"])
    S.append(f"""<section id="ignorar"><h2><span class="n">5</span>Pode ignorar</h2>
{'<ul>' + ig + '</ul>' if ig else '<p class="vazio">Nada nesta semana.</p>'}</section>""")
    S.append(f"""<section id="travou"><h2><span class="n">6</span>Travou?</h2>
<p>{e(ed['travou'] or pl.get('texto', 'Pergunte no grupo com o print do erro.'))}</p>{('<p>' + a(pl['link']) + '</p>') if pl.get('link') else ''}</section>""")
    if ajudantes:
        aj = "<ol class=\"rank\">" + "".join(f"<li><strong>{e(x['nome'])}</strong> — {e(x['nota'])}</li>" for x in ajudantes[:5]) + "</ol>"
    else:
        aj = f"<p class=\"vazio\">{e(cfg.get('ajudantes_vazio', 'Ranking desta semana ainda vazio: anote em ajudantes.md quem respondeu dúvidas no grupo.'))}</p>"
    S.append(f"""<section id="ajudou"><h2><span class="n">7</span>Quem mais ajudou</h2>{aj}</section>""")
    S.append(f"""<footer>{e(nome)} · {a(cfg.get('link', ''), cfg.get('link', '').replace('https://', ''))}<br>
Feito com o kit semana-inema · gerado em {dt.date.today().strftime('%d/%m/%Y')}</footer></div></body></html>""")
    return "\n".join(S) + "\n"


def html_email(ed, cfg, jan, chegou, vitorias, ajudantes):
    nome = cfg.get("comunidade", "Comunidade")
    u = ed["unica"]
    pl = cfg.get("plantao", {})
    lk = 'style="color:#854d0e;text-decoration:underline"'

    def link(url, txt=None):
        if not url:
            return e(txt or "")
        return f'<a href="{e(url)}" {lk}>{e(txt or url)}</a>'

    def h2(n, t):
        return (f'<h2 style="font:700 18px/1.3 Arial,sans-serif;margin:28px 0 10px;color:#1a1a22">'
                f'{n}. {e(t)}</h2>')

    def lista(itens):
        return '<ul style="margin:0;padding-left:20px">' + "".join(
            f'<li style="margin:6px 0">{x}</li>' for x in itens) + "</ul>"

    mx = int(cfg.get("max_o_que_chegou_email", 15))
    corpo = []
    corpo.append(f'<p style="margin:0;color:#5b5b68;font-size:13px;letter-spacing:.08em;text-transform:uppercase">'
                 f'{e(nome)} · {data_br(jan[0])} a {data_br(jan[1])}/{jan[1].year}</p>')
    corpo.append(f'<h1 style="font:800 26px/1.2 Arial,sans-serif;margin:6px 0 8px;color:#1a1a22">'
                 f'{e(cfg.get("titulo_pagina", "A semana sem sobrecarga"))}</h1>')
    corpo.append(f'<p style="margin:0 0 8px;color:#5b5b68">{e(ed["abertura"] or "Uma coisa só para fazer. O resto pode esperar.")}</p>')
    bloco = [f'<p style="font:700 20px/1.3 Arial,sans-serif;margin:0 0 8px">{e(u["titulo"])}</p>']
    if u["porque"]:
        bloco.append(f'<p style="margin:4px 0"><b>Por quê:</b> {e(u["porque"])}</p>')
    if u["resultado"]:
        bloco.append(f'<p style="margin:4px 0"><b>Pronto quando:</b> {e(u["resultado"])}</p>')
    if u["tempo"]:
        bloco.append(f'<p style="margin:4px 0"><b>Tempo:</b> {e(u["tempo"])}</p>')
    if u["link"]:
        bloco.append(f'<p style="margin:14px 0 0"><a href="{e(u["link"])}" style="background:#FACC15;color:#1a1206;'
                     f'padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:700;display:inline-block">Comece aqui</a></p>')
    corpo.append(h2(1, "A única coisa desta semana"))
    corpo.append('<div style="border:2px solid #EAB308;background:#FEF9C3;border-radius:14px;padding:16px">' + "".join(bloco) + "</div>")
    corpo.append(h2(2, "Seu caso → seu caminho"))
    corpo.append(lista([f"<b>{e(c['usa'])}</b> → {link(c['link'], c['veja']) if c['link'] else e(c['veja'])}" for c in ed["caso"]])
                 if ed["caso"] else "<p>Sem tabela nesta edição.</p>")
    corpo.append(h2(3, "Vitórias da comunidade"))
    corpo.append(lista([f"<b>{e(v['nome'])}</b> — {e(v['feito'])}" + (f" · {link(v['link'], 'ver')}" if v["link"] else "") for v in vitorias])
                 if vitorias else "<p>Ainda sem vitórias nesta edição. Fez algo funcionar? Responda este e-mail.</p>")
    corpo.append(h2(4, f"O que chegou ({len(chegou)} na semana)"))
    itens = [f"{data_br(it['data'])} · {link(it['link'], it['titulo']) if it['link'] else e(it['titulo'])}" for it in chegou[:mx]]
    if len(chegou) > mx:
        itens.append(f"e mais {len(chegou) - mx} na página da semana.")
    corpo.append(lista(itens) if itens else "<p>Nada novo nas fontes nesta semana.</p>")
    corpo.append(h2(5, "Pode ignorar"))
    corpo.append(lista([e(x) for x in ed["ignorar"]]) if ed["ignorar"] else "<p>Nada nesta semana.</p>")
    corpo.append(h2(6, "Travou?"))
    corpo.append(f'<p>{e(ed["travou"] or pl.get("texto", ""))}' + (f'<br>{link(pl["link"])}' if pl.get("link") else "") + "</p>")
    corpo.append(h2(7, "Quem mais ajudou"))
    corpo.append(lista([f"{k}º <b>{e(x['nome'])}</b> — {e(x['nota'])}" for k, x in enumerate(ajudantes[:5], 1)]) if ajudantes
                 else f"<p>{e(cfg.get('ajudantes_vazio', 'Ranking desta semana ainda vazio.'))}</p>")
    corpo.append(f'<p style="margin-top:32px;color:#5b5b68;font-size:13px">{e(nome)} · {link(cfg.get("link", ""))}</p>')
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Semana {e(nome)}</title></head><body style="margin:0;background:#f6f7f9">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f7f9"><tr><td align="center" style="padding:20px 12px">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border:1px solid #e1e3ea;border-radius:14px">'
            f'<tr><td style="padding:24px 22px;font:16px/1.6 Arial,sans-serif;color:#1a1a22">{"".join(corpo)}</td></tr></table>'
            f'</td></tr></table></body></html>\n')


# ---------------------------------------------------------------- rascunho

def texto_rascunho(cfg, jan, chegou, resumo, vitorias, ajudantes):
    L = [f"# Rascunho da semana — {cfg.get('comunidade', '')} — {jan[0].isoformat()} a {jan[1].isoformat()}", ""]
    L.append("Próximo passo: abra o Claude Code ou o Codex nesta pasta do kit e cole o pedido de "
             "`prompts/escolher-a-unica-coisa.md`. Ele lê este rascunho e preenche o `edicao.md`.")
    L.append("Depois: `python3 semana.py gerar` (com o mesmo --ate/--de).")
    L.append("")
    L.append("## Fontes lidas")
    for nome, c in resumo:
        L.append(f"- {nome}: " + ", ".join(f"{k}={v}" for k, v in c.items()))
    L.append("")
    L.append(f"## O que chegou ({len(chegou)} itens na janela)")
    for k, it in enumerate(chegou, 1):
        L.append(f"{k}. {it['data'].isoformat()} · {it['titulo']}" + (f" — {corta(it['detalhe'], 160)}" if it["detalhe"] and cfg.get("mostrar_detalhe") else "")
                 + (f" · {it['link']}" if it["link"] else "") + f" · fonte: {it['fonte']}")
    L.append("")
    L.append(f"## Vitórias ({len(vitorias)})")
    for v in vitorias:
        L.append(f"- {v['nome']} — {v['feito']}" + (f" — {v['link']}" if v["link"] else ""))
    L.append("")
    L.append(f"## Ajudantes ({len(ajudantes)})")
    for x in ajudantes:
        L.append(f"- {x['nome']} — {x['nota']}")
    L.append("")
    L.append("## Modelo do edicao.md (copie, preencha e salve como edicao.md)")
    L.append("```markdown")
    L.append(MODELO_EDICAO.strip().replace("(o último dia da semana, AAAA-MM-DD — o mesmo --ate do rascunho)", jan[1].isoformat()))
    L.append("```")
    return "\n".join(L) + "\n"


MODELO_EDICAO = """
# Edição da semana

## Abertura
(1 frase curta, opcional)

## A única coisa
semana: (o último dia da semana, AAAA-MM-DD — o mesmo --ate do rascunho)
título: (a tarefa, com verbo: "Faça…", "Monte…", "Rode…")
por que: (1 frase: o que muda na vida de quem fizer)
resultado: (o que a pessoa tem FUNCIONANDO no fim — não "assistiu o vídeo")
tempo: (ex.: 40 minutos)
link: (o guia ou o vídeo que leva até lá)

## Seu caso → seu caminho
| Seu caso | Veja |
|---|---|
| (ex.: Usa ChatGPT no dia a dia) | [título](link) |

## Pode ignorar
- (novidade) — (por que dá para deixar para depois)

## Travou?
(opcional: se vazio, usa o texto do plantão do config.json)
"""


# ---------------------------------------------------------------- comandos

def carregar(args):
    cfg_path = Path(args.config).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    base = cfg_path.parent
    ate = dt.date.fromisoformat(args.ate) if args.ate else dt.date.today()
    de = dt.date.fromisoformat(args.de) if args.de else None
    jan = janela(ate, args.dias or int(cfg.get("janela_dias", 7)), de)
    chegou, resumo = coletar(cfg, base, jan)
    vp = caminho(base, args.vitorias or cfg.get("vitorias", "vitorias.md"))
    ap = caminho(base, args.ajudantes or cfg.get("ajudantes", "ajudantes.md"))
    vitorias = ler_vitorias(vp.read_text(encoding="utf-8")) if vp.exists() else []
    ajudantes = ler_ajudantes(ap.read_text(encoding="utf-8")) if ap.exists() else []
    pasta = caminho(base, args.saida or cfg.get("saida", "saida")) / jan[1].isoformat()
    return cfg, base, jan, chegou, resumo, vitorias, ajudantes, pasta


def avisa_fontes(resumo):
    faltam = [c["ARQUIVO_NAO_ENCONTRADO"] for _, c in resumo if "ARQUIVO_NAO_ENCONTRADO" in c]
    if faltam:
        print("\nATENÇÃO: fonte não encontrada, \"O que chegou\" saiu sem ela: " + ", ".join(faltam))
        print("Confira o 'caminho' em config.json (para testar o exemplo: --config config.exemplo.json).")
    elif not resumo:
        print("\nATENÇÃO: nenhuma fonte ativa em config.json; \"O que chegou\" saiu vazio.")


def cmd_rascunho(args):
    cfg, base, jan, chegou, resumo, vitorias, ajudantes, pasta = carregar(args)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "rascunho.md").write_text(texto_rascunho(cfg, jan, chegou, resumo, vitorias, ajudantes), encoding="utf-8")
    print(f"Janela: {jan[0].isoformat()} a {jan[1].isoformat()} ({(jan[1] - jan[0]).days + 1} dias)")
    for nome, c in resumo:
        print(f"  fonte {nome}: " + ", ".join(f"{k}={v}" for k, v in c.items()))
    print(f"O que chegou: {len(chegou)} itens · vitórias: {len(vitorias)} · ajudantes: {len(ajudantes)}")
    print(f"Rascunho: {pasta / 'rascunho.md'}")
    print("Agora: cole prompts/escolher-a-unica-coisa.md no Claude Code/Codex para preencher o edicao.md.")
    avisa_fontes(resumo)
    return 0


def cmd_gerar(args):
    cfg, base, jan, chegou, resumo, vitorias, ajudantes, pasta = carregar(args)
    ep = caminho(base, args.edicao or cfg.get("edicao", "edicao.md"))
    if not ep.exists():
        print(f"Falta o {ep}. Rode `semana.py rascunho` e preencha a edição (ou use o prompt).", file=sys.stderr)
        return 2
    ed = ler_edicao(ep.read_text(encoding="utf-8"))
    sem = ed["unica"].get("semana", "")
    if sem != jan[1].isoformat() and not args.forcar:
        print(f"O {ep.name} é da semana '{sem or '(sem data)'}', e você está gerando a semana que termina em "
              f"{jan[1].isoformat()}.\nPreencha a edição desta semana (linha 'semana: {jan[1].isoformat()}' em "
              "'## A única coisa') ou use --forcar.", file=sys.stderr)
        return 2
    if not ed["unica"]["titulo"]:
        print(f"O {ep} não tem 'título:' em '## A única coisa'. Sem a única coisa não há edição.", file=sys.stderr)
        return 2
    pasta.mkdir(parents=True, exist_ok=True)
    limite = int(cfg.get("limite_telegram", LIMITE_TELEGRAM))
    tg = texto_telegram(ed, cfg, jan, chegou, vitorias, ajudantes)
    partes = dividir(tg, limite)
    for velho in pasta.glob("telegram*.md"):
        velho.unlink()
    nomes = []
    for k, p in enumerate(partes, 1):
        nome = "telegram.md" if k == 1 else f"telegram-{k}.md"
        (pasta / nome).write_text(p.strip("\n") + "\n", encoding="utf-8")
        nomes.append((nome, u16(p.strip("\n"))))
    (pasta / "email.html").write_text(html_email(ed, cfg, jan, chegou, vitorias, ajudantes), encoding="utf-8")
    (pasta / "pagina.html").write_text(html_pagina(ed, cfg, jan, chegou, vitorias, ajudantes), encoding="utf-8")
    print(f"Janela: {jan[0].isoformat()} a {jan[1].isoformat()} ({(jan[1] - jan[0]).days + 1} dias)")
    print(f"A única coisa: {ed['unica']['titulo']}")
    print(f"O que chegou: {len(chegou)} · vitórias: {len(vitorias)} · ajudantes: {len(ajudantes)} · pode ignorar: {len(ed['ignorar'])}")
    print(f"Telegram: {u16(tg)} caracteres no total → {len(partes)} mensagem(ns): "
          + ", ".join(f"{n} ({c})" for n, c in nomes))
    print(f"Arquivos em {pasta}: " + ", ".join([n for n, _ in nomes] + ["email.html", "pagina.html"]))
    print("Nada foi publicado. Cole/publique você mesmo.")
    avisa_fontes(resumo)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="A semana sem sobrecarga — post semanal da comunidade.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("rascunho", "gerar"):
        p = sub.add_parser(nome)
        p.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
        p.add_argument("--ate", help="último dia da semana (AAAA-MM-DD); padrão: hoje")
        p.add_argument("--de", help="primeiro dia (AAAA-MM-DD); padrão: ate − (dias − 1)")
        p.add_argument("--dias", type=int, help="tamanho da janela; padrão: janela_dias do config (7)")
        p.add_argument("--saida")
        p.add_argument("--vitorias")
        p.add_argument("--ajudantes")
        if nome == "gerar":
            p.add_argument("--edicao")
            p.add_argument("--forcar", action="store_true", help="gera mesmo se a edicao.md for de outra semana")
    args = ap.parse_args(argv)
    return cmd_rascunho(args) if args.cmd == "rascunho" else cmd_gerar(args)


if __name__ == "__main__":
    sys.exit(main())
