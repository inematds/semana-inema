# semana-inema — a semana sem sobrecarga

[![semana-inema](guia/assets/banner.jpg)](https://inematds.github.io/semana-inema/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

O semana-inema é um kit gratuito para quem cuida de uma comunidade (grupo de Telegram, WhatsApp, turma, lista de e-mail). Toda semana ele lê o que saiu de novo nas suas fontes e monta uma edição curta com sete partes: a única coisa a fazer, o caminho para cada caso, as vitórias dos membros, o que chegou, o que pode ignorar, onde pedir ajuda e quem mais ajudou. Sai em três formatos: mensagem de Telegram, e-mail e página. Precisa só de Python no computador; nada é publicado sozinho.

> Sua comunidade não precisa de mais conteúdo. Precisa saber o que fazer.

## 📖 Guia de uso

Guia completo (o método + passo a passo): **https://inematds.github.io/semana-inema/guia/**

## O processo, do início ao fim

Quem faz: 🧠 o moderador (você) · ⚙️ o script · 🤖 um agente (Claude Code ou Codex), opcional.

| # | Passo | Comando / arquivo | Quem |
|---|---|---|---|
| 1 | Configurar uma vez: nome, link, plantão e fontes | `config.json` | 🧠 |
| 2 | Durante a semana, anotar vitórias e quem ajudou (com licença das pessoas) | `vitorias.md`, `ajudantes.md` | 🧠 |
| 3 | Juntar o que chegou na semana e montar o rascunho | `python3 semana.py rascunho` → `saida/<data>/rascunho.md` | ⚙️ |
| 4 | Escolher a única coisa, a tabela "seu caso → seu caminho" e o "pode ignorar" | colar `prompts/escolher-a-unica-coisa.md` → escreve `edicao.md` | 🤖 (ou 🧠 à mão) |
| 5 | Ler e ajustar a escolha | `edicao.md` | 🧠 |
| 6 | Gerar os três formatos | `python3 semana.py gerar` → `telegram.md` (+ `telegram-2.md`…), `email.html`, `pagina.html` | ⚙️ |
| 7 | Conferir e publicar (o kit não envia nada) | colar no grupo, no e-mail, no site | 🧠 |

Para uma semana que não termina hoje, passe as datas nos passos 3 e 6: `--ate AAAA-MM-DD` (último dia) e, se quiser, `--de AAAA-MM-DD`. Sem `--de`, a janela é de 7 dias terminando no `--ate`.

## Começar

```bash
git clone https://github.com/inematds/semana-inema.git
cd semana-inema
python3 -m unittest discover -s tests      # tem que terminar com OK
python3 semana.py rascunho
python3 semana.py gerar
```

Só biblioteca padrão do Python 3 (nada de `pip install`). No Windows, troque `python3` por `py`.

## As sete seções

1. **A única coisa desta semana** — uma tarefa que termina com 1 resultado funcionando (não "assisti o vídeo").
2. **Seu caso → seu caminho** — tabela "usa X → veja Y".
3. **Vitórias da comunidade** — de `vitorias.md`: `- Nome — o que fez — link`.
4. **O que chegou** — lido das fontes, só o que caiu na janela da semana.
5. **Pode ignorar** — 2 a 4 novidades que podem esperar, com o motivo.
6. **Travou?** — onde e como pedir ajuda (texto do plantão no `config.json`).
7. **Quem mais ajudou** — ranking manual de `ajudantes.md` (opcional; vazio aparece como vazio).

## Fontes de "O que chegou" (`config.json` › `fontes`)

| tipo | O que lê | Campos |
|---|---|---|
| `tabela_md` | Tabela Markdown de publicações. Entra a linha cujo estado começa com a palavra de `so_com` (no INEMA, "publicad", que vale para publicado e publicada; em inglês, "published"); a data é a escrita depois dessa palavra (dd/mm ou dd/mm/aaaa) ou, se faltar, a da coluna de data. Linhas sem data ficam de fora e são contadas. | `caminho`, `coluna_titulo`, `coluna_data`, `coluna_estado`, `so_com`, `padrao_id_youtube` (opcional) |
| `git_log` | Commits dos repositórios listados, na janela da semana (sem merges). | `repos`, `ignorar_prefixos`, `link_repo` |
| `feed` | Arquivo salvo no disco: JSON (`titulo`/`data`/`link`) ou RSS/Atom. URL não é lida (o kit não usa rede). | `caminho` |

Cada fonte liga e desliga com `"ativo": true/false`.

## Telegram: limite de 4.096

O texto do Telegram é contado como o Telegram conta (unidades UTF-16: emoji vale 2). Se passar de 4.096, o kit divide em `telegram.md`, `telegram-2.md`… cortando de preferência no início de uma seção. O teste `tests/test_semana.py` confere que nenhuma parte passa do limite e que nada se perde.

## Exemplo real: a semana do INEMA (01 a 08/11/2026)

Em [`exemplos/2026-11-08/`](exemplos/2026-11-08/): `rascunho.md`, `telegram.md`, `email.html`, `pagina.html` e prints em 1440 px e 390 px. O kit vem configurado para o INEMA (lê a tabela de produções de vídeo do INEMA); troque o `config.json` para a sua comunidade.

- Tabela lida (08/11/2026): 90 linhas, 50 publicadas com data, **26 na semana**.
- A única coisa: *Responda as 6 perguntas da Escada do Negócio com IA e escolha UM negócio para começar.*
- Telegram: 3.671 caracteres, 1 mensagem.
- Vitórias do exemplo: entregas do próprio INEMA, marcadas "(exemplo)". Ajudantes: vazio (o kit não inventa nomes).

Comandos usados:

```bash
python3 semana.py rascunho --de 2026-11-01 --ate 2026-11-08 --saida exemplos
python3 semana.py gerar    --de 2026-11-01 --ate 2026-11-08 --saida exemplos
```

## Arquivos

| Arquivo | Para quê |
|---|---|
| `semana.py` | o script (rascunho e gerar) |
| `config.json` | comunidade, link, plantão, fontes (vem com o INEMA) |
| `vitorias.md`, `ajudantes.md` | o que o moderador anota na semana |
| `edicao.md` | a escolha da semana (única coisa, seu caso, pode ignorar) |
| `prompts/escolher-a-unica-coisa.md` | pedido pronto para o Claude Code ou o Codex |
| `tests/` | testes sem rede (`python3 -m unittest discover -s tests`) |
| `exemplos/` | a edição real do INEMA |
| `guia/` | página de apresentação e guia (PT/EN/ES) |

## Licença

MIT. Feito pelo [INEMA.CLUB](https://inema.club).
