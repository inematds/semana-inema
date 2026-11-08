# semana-inema — a week without overload

[![semana-inema](guia/assets/banner-en.jpg)](https://inematds.github.io/semana-inema/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

semana-inema is a free kit for anyone who runs a community (Telegram group, WhatsApp group, class, email list). Every week, it reads what’s new in your sources and puts together a short edition with seven parts: the one thing to do, a path for each case, members’ wins, what’s new, what you can ignore, where to ask for help, and who helped the most. It comes in three formats: Telegram message, email, and webpage. You only need Python on your computer; nothing is published automatically.

> Your community doesn’t need more content. It needs to know what to do.

## 📖 User guide

Complete guide (the method + step-by-step instructions): **https://inematds.github.io/semana-inema/guia/en/**

## The process, from start to finish

Who does what: 🧠 the moderator (you) · ⚙️ the script · 🤖 an agent (Claude Code or Codex), optional.

| # | Step | Command / file | Who |
|---|---|---|---|
| 1 | View the ready-made example (reads the INEMA week copy included in the kit) | `python3 semana.py gerar --config config.exemplo.json --de 2026-11-01 --ate 2026-11-08` | ⚙️ |
| 2 | Set up once: name, link, help text (the text in the "Stuck?" section), and your published items table | `cp config.modelo.json config.json`, then `config.json` and `publicados.md` | 🧠 |
| 3 | During the week, note wins and who helped (with people’s permission) | `vitorias.md`, `ajudantes.md` | 🧠 |
| 4 | Gather what came in during the week and build the draft | `python3 semana.py rascunho` → `saida/<data>/rascunho.md` | ⚙️ |
| 5 | Choose the one thing, the "your case → your path" table, and what people can ignore | paste `prompts/escolher-a-unica-coisa.md` → write `edicao.md` | 🤖 (or 🧠 by hand) |
| 6 | Review and adjust the choices (the `semana:` line must be the last day of the week; editions for other weeks are rejected) | `edicao.md` | 🧠 |
| 7 | Generate the three formats | `python3 semana.py gerar` → `telegram.md` (`telegram-2.md`… if needed), `email.html`, `pagina.html` | ⚙️ |
| 8 | Review and publish (the kit doesn’t send anything) | paste into the group, email, or website | 🧠 |

For a week that doesn’t end today, pass the dates in steps 4 and 7: `--ate YYYY-MM-DD` (last day) and, if you want, `--de YYYY-MM-DD`. Without `--de`, the window is 7 days ending on `--ate`.

## Getting started

```bash
git clone https://github.com/inematds/semana-inema.git
cd semana-inema
python3 -m unittest discover -s tests
python3 semana.py gerar --config config.exemplo.json --de 2026-11-01 --ate 2026-11-08
```

Then, for your community: create `publicados.md`, copy the generic template over the config (`cp config.modelo.json config.json`; on Windows, `copy`), change the name, link and help text in it, delete the examples in `vitorias.md`/`ajudantes.md`, and run:

```bash
python3 semana.py rascunho
python3 semana.py gerar
```

`publicados.md` format (one line per publication; items without "published" are excluded):

```markdown
| Tema | Data | Estado |
|---|---|---|
| Aula: o primeiro agente | 05/11/2026 | publicado 05/11/2026 — https://exemplo.com/aula |
| Guia do backup | 06/11/2026 | em produção |
```

Python 3 standard library only (no `pip install`). On Windows, replace `python3` with `py`.

## The seven sections

1. **The one thing to do this week** — one task that ends with one working result (not "I watched the video").
2. **Your case → your path** — a "use X → see Y" table.
3. **Community wins** — from `vitorias.md`: `- Name — what they did — link`.
4. **What’s new** — read from the sources, only what falls within the week’s window.
5. **You can ignore this** — 2 to 4 updates that can wait, with a reason.
6. **Stuck?** — where and how to ask for help (the help text in `config.json`).
7. **Who helped the most** — a manual ranking from `ajudantes.md` (optional; if empty, it appears empty).

## Sources for "What’s new" (`config.json` › `fontes`)

| type | What it reads | Fields |
|---|---|---|
| `tabela_md` | Markdown table of published items. A row is included when its status starts with the word in `so_com` (in INEMA, "published"); the date is the one written after that word (dd/mm or dd/mm/yyyy), or, if missing, the date in the date column. Rows without a date are excluded and counted. | `caminho`, `coluna_titulo`, `coluna_data`, `coluna_estado`, `so_com`, `padrao_id_youtube` (optional) |
| `git_log` | Commits from the listed repositories, within the week’s window (excluding merges). | `repos`, `ignorar_prefixos`, `link_repo` |
| `feed` | File saved on disk: JSON (`titulo`/`data`/`link`) or RSS/Atom. URLs are not read (the kit does not use the network). | `caminho` |

Each source can be enabled or disabled with `"ativo": true/false`.

## Telegram: 4,096-character limit

Telegram text is counted the way Telegram counts it (UTF-16 units: an emoji counts as 2). If it exceeds 4,096, the kit splits it into `telegram.md`, `telegram-2.md`… preferably at the start of a section. The `tests/test_semana.py` test checks that no part exceeds the limit and that nothing is lost.

## Real example: the INEMA week (Nov 1–8, 2026)

In [`exemplos/2026-11-08/`](exemplos/2026-11-08/): `publicados.md` (clean copy of the week), `rascunho.md`, `telegram.md`, `email.html`, `pagina.html`, and screenshots at 1440 px and 390 px. The kit comes configured for INEMA (it reads INEMA’s video production table); change `config.json` for your community.

- Table read (Nov 8, 2026): 90 rows, 50 published with a date, **26 during the week**.
- The one thing: *Answer the 6 questions in the AI Business Ladder and choose ONE business to start with.* (in Portuguese in the example)
- Telegram: 3,671 characters, 1 message.
- Example wins: deliveries by INEMA itself, marked "(exemplo)". Helpers: empty (the kit doesn’t make up names).

Commands used:

```bash
python3 semana.py rascunho --de 2026-11-01 --ate 2026-11-08 --saida exemplos
python3 semana.py gerar    --de 2026-11-01 --ate 2026-11-08 --saida exemplos
```

## Files

| File | Purpose |
|---|---|
| `semana.py` | the script (draft and generate) |
| `config.json` | community, link, help text, sources (comes with INEMA settings; reads the internal production table) |
| `config.exemplo.json` | runs the example in any clone (reads `exemplos/2026-11-08/publicados.md`) |
| `config.modelo.json` | generic template for your community (reads `publicados.md`); copy it over `config.json` |
| `vitorias.md`, `ajudantes.md` | what the moderator notes during the week |
| `edicao.md` | the week’s choices (the one thing, your case, what you can ignore); the included file is the INEMA example |
| `prompts/escolher-a-unica-coisa.md` | ready-to-use prompt for Claude Code or Codex |
| `tests/` | tests without network access (`python3 -m unittest discover -s tests`) |
| `exemplos/` | the real INEMA edition |
| `guia/` | presentation and guide page (PT/EN/ES) |

## Language

The post comes out in Portuguese: the section titles are written in `semana.py` (`texto_telegram`, `html_pagina`, `html_email`). Translate them there if your community speaks another language. The `edicao.md` can already use English headings (`## The one thing`, `## Your case → your path`, `## You can ignore`).

## License

MIT. Made by [INEMA.CLUB](https://inema.club).