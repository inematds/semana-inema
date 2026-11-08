# semana-inema — the week without overload

[![semana-inema](guia/assets/banner-en.jpg)](https://inematds.github.io/semana-inema/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

semana-inema is a free kit for anyone who runs a community (Telegram or WhatsApp group, class, email list). Every week, it reads what’s new in your sources and puts together a short edition with seven parts: the one thing to do, the path for each case, members’ wins, what arrived, what you can ignore, where to ask for help, and who helped the most. It comes in three formats: Telegram message, email, and webpage. You only need Python on your computer; nothing is published automatically.

> Your community doesn’t need more content. It needs to know what to do.

## 📖 User guide

Complete guide (the method + step-by-step instructions): **https://inematds.github.io/semana-inema/guia/en/**

## The process, from start to finish

Who does what: 🧠 the moderator (you) · ⚙️ the script · 🤖 an agent (Claude Code or Codex), optional.

| # | Step | Command / file | Who |
|---|---|---|---|
| 1 | Set up once: name, link, help desk, and sources | `config.json` | 🧠 |
| 2 | During the week, note wins and who helped (with people’s consent) | `vitorias.md`, `ajudantes.md` | 🧠 |
| 3 | Gather what arrived during the week and create a draft | `python3 semana.py rascunho` → `saida/<data>/rascunho.md` | ⚙️ |
| 4 | Choose the one thing, the "your case → your path" table, and what you can ignore | Paste `prompts/escolher-a-unica-coisa.md` → writes `edicao.md` | 🤖 (or 🧠 by hand) |
| 5 | Review and adjust the choices | `edicao.md` | 🧠 |
| 6 | Generate the three formats | `python3 semana.py gerar` → `telegram.md` (+ `telegram-2.md`…), `email.html`, `pagina.html` | ⚙️ |
| 7 | Review and publish (the kit doesn’t send anything) | Paste into the group, email, or website | 🧠 |

For a week that doesn’t end today, pass the dates in steps 3 and 6: `--ate YYYY-MM-DD` (last day) and, if you want, `--de YYYY-MM-DD`. Without `--de`, the window is 7 days ending on `--ate`.

## Get started

```bash
git clone https://github.com/inematds/semana-inema.git
cd semana-inema
python3 -m unittest discover -s tests      # must finish with OK
python3 semana.py rascunho
python3 semana.py gerar
```

Python 3 standard library only (no `pip install`). On Windows, replace `python3` with `py`.

## The seven sections

1. **The one thing this week** — one task that ends with 1 working result (not "watched the video").
2. **Your case → your path** — a "use X → see Y" table.
3. **Community wins** — from `vitorias.md`: `- Name — what they did — link`.
4. **What arrived** — read from the sources, only what falls within the week’s window.
5. **You can ignore this** — 2 to 4 updates that can wait, with the reason.
6. **Stuck?** — where and how to ask for help (help desk text in `config.json`).
7. **Who helped the most** — manual ranking from `ajudantes.md` (optional; if empty, it appears empty).

## Sources for "What arrived" (`config.json` › `fontes`)

| type | What it reads | Fields |
|---|---|---|
| `tabela_md` | Markdown table of publications. A row is included when its status begins with "publicad" (the Portuguese word used in INEMA); in English, set `so_com` to "published". The date is the one written after that word (dd/mm or dd/mm/yyyy) or, if missing, the date column. Rows without a date are excluded and counted. | `caminho`, `coluna_titulo`, `coluna_data`, `coluna_estado`, `so_com`, `padrao_id_youtube` (optional) |
| `git_log` | Commits from the listed repositories, within the week’s window (excluding merges). | `repos`, `ignorar_prefixos`, `link_repo` |
| `feed` | File saved on disk: JSON (`titulo`/`data`/`link`) or RSS/Atom. URLs are not read (the kit doesn’t use the network). | `caminho` |

Each source can be turned on or off with `"ativo": true/false`.

## Telegram: 4,096 character limit

Telegram text is counted the way Telegram counts it (UTF-16 units: each emoji counts as 2). If it exceeds 4,096, the kit splits it into `telegram.md`, `telegram-2.md`… preferably at the start of a section. The `tests/test_semana.py` test checks that no part exceeds the limit and that nothing is lost.

## Real example: the INEMA week (Nov 1–8, 2026)

In [`exemplos/2026-11-08/`](exemplos/2026-11-08/): `rascunho.md`, `telegram.md`, `email.html`, `pagina.html`, and screenshots at 1440 px and 390 px. The kit comes configured for INEMA (it reads INEMA’s video production table); change `config.json` for your community.

- Table read (Nov 8, 2026): 90 rows, 50 published with a date, **26 during the week**.
- The one thing: *Answer the 6 questions in the AI Business Ladder and choose ONE business to start with.* (in Portuguese in the example)
- Telegram: 3,671 characters, 1 message.
- Example wins: INEMA’s own deliveries, marked "(example)". Helpers: empty (the kit doesn’t make up names).

Commands used:

```bash
python3 semana.py rascunho --de 2026-11-01 --ate 2026-11-08 --saida exemplos
python3 semana.py gerar    --de 2026-11-01 --ate 2026-11-08 --saida exemplos
```

## Files

| File | Purpose |
|---|---|
| `semana.py` | the script (draft and generate) |
| `config.json` | community, link, help desk, sources (comes with INEMA) |
| `vitorias.md`, `ajudantes.md` | what the moderator notes during the week |
| `edicao.md` | the week’s choices (one thing, your case, ignore this) |
| `prompts/escolher-a-unica-coisa.md` | ready-to-use prompt for Claude Code or Codex |
| `tests/` | offline tests (`python3 -m unittest discover -s tests`) |
| `exemplos/` | INEMA’s real edition |
| `guia/` | presentation and guide page (PT/EN/ES) |

## License

MIT. Made by [INEMA.CLUB](https://inema.club).