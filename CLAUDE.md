# CLAUDE.md — semana-inema

Kit que monta o post semanal de uma comunidade ("a semana sem sobrecarga"): `semana.py rascunho` → escolha em `edicao.md` → `semana.py gerar` (telegram.md ≤ 4.096 UTF-16, email.html, pagina.html). Só stdlib, sem rede, não publica nada.

## Regras do projeto

- Autor dos commits: `inematds <inematds@gmail.com>` (repo `inematds/semana-inema`).
- Testes: `python3 -m unittest discover -s tests` — sem rede, sem ler nada fora de `tests/`. Mudou o parser ou a divisão do Telegram → teste junto.
- Nunca inventar vitória, ajudante ou membro. Exemplo INEMA = só entregas reais do próprio INEMA, marcadas "(exemplo)".
- O kit não envia, não posta e não lê conversas. Publicar é sempre do moderador.
- Projeto sem fonte: não citar material de referência, autor ou comunidade de onde a ideia veio (README, guia, commits).
- Guia em `guia/` PT + `guia/en/` + `guia/es/`; tradução pelo `inema-traduz`; mudou o PT, retraduzir o trecho nos dois.
- Página e guia sem rolagem lateral: medir `scrollWidth` de 360 a 1920 px antes do push.

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule at the TOP of the Lessons list below, so it never happens again.

## Lessons

- `overflow-x:hidden` no html/body esconde a rolagem lateral e engana a medição de `scrollWidth`; não usar como conserto — achar o elemento que vaza (nav do guia estourava em 800 px). (08/11/2026)
- PRODUCOES-VIDEO.md tem uma linha de dados ACIMA do cabeçalho, linhas sem data e data do dono ≠ data de publicação: a data vem do "publicado DD/MM" do estado; o teste com fixture cobre isso. (08/11/2026)
