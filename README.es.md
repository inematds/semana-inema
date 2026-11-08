# semana-inema — la semana sin sobrecarga

[![semana-inema](guia/assets/banner-es.jpg)](https://inematds.github.io/semana-inema/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

semana-inema es un kit gratuito para quienes cuidan una comunidad (grupo de Telegram, WhatsApp, clase, lista de correo). Cada semana revisa lo nuevo en tus fuentes y prepara una edición breve con siete partes: lo único que tienes que hacer, el camino para cada caso, las victorias de los miembros, lo que llegó, lo que puedes ignorar, dónde pedir ayuda y quién ayudó más. Se genera en tres formatos: mensaje de Telegram, correo electrónico y página. Solo necesitas Python en tu computadora; nada se publica automáticamente.

> Tu comunidad no necesita más contenido. Necesita saber qué hacer.

## 📖 Guía de uso

Guía completa (el método + paso a paso): **https://inematds.github.io/semana-inema/guia/es/**

## El proceso, de principio a fin

Quién lo hace: 🧠 el moderador (tú) · ⚙️ el script · 🤖 un agente (Claude Code o Codex), opcional.

| # | Paso | Comando / archivo | Quién |
|---|---|---|---|
| 1 | Ver el ejemplo listo (lee la copia de la semana del INEMA que viene en el kit) | `python3 semana.py gerar --config config.exemplo.json --de 2026-11-01 --ate 2026-11-08` | ⚙️ |
| 2 | Configurar una vez: nombre, enlace, texto de ayuda de la sección "¿Te trabaste?" y tu tabla de publicaciones | `cp config.modelo.json config.json`, después `config.json` y `publicados.md` | 🧠 |
| 3 | Durante la semana, anotar las victorias y quién ayudó (con permiso de las personas) | `vitorias.md`, `ajudantes.md` | 🧠 |
| 4 | Reunir lo que llegó durante la semana y preparar el borrador | `python3 semana.py rascunho` → `saida/<data>/rascunho.md` | ⚙️ |
| 5 | Elegir lo único que hay que hacer, la tabla "tu caso → tu camino" y lo que "puedes ignorar" | pegar `prompts/escolher-a-unica-coisa.md` → escribe `edicao.md` | 🤖 (o 🧠 a mano) |
| 6 | Leer y ajustar la elección (la línea `semana:` debe tener el último día de la semana; se rechazan las ediciones de otra semana) | `edicao.md` | 🧠 |
| 7 | Generar los tres formatos | `python3 semana.py gerar` → `telegram.md` (`telegram-2.md`…), `email.html`, `pagina.html` | ⚙️ |
| 8 | Revisar y publicar (el kit no envía nada) | pegar en el grupo, en el correo, en el sitio | 🧠 |

Para una semana que no termina hoy, pasa las fechas en los pasos 4 y 7: `--ate AAAA-MM-DD` (último día) y, si quieres, `--de AAAA-MM-DD`. Sin `--de`, el período abarca 7 días y termina en `--ate`.

## Empezar

```bash
git clone https://github.com/inematds/semana-inema.git
cd semana-inema
python3 -m unittest discover -s tests
python3 semana.py gerar --config config.exemplo.json --de 2026-11-01 --ate 2026-11-08
```

Después, para tu comunidad: crea `publicados.md`, copia la plantilla genérica sobre la configuración (`cp config.modelo.json config.json`; en Windows, `copy`), cambia en ella el nombre, el enlace y el texto de ayuda, borra los ejemplos de `vitorias.md`/`ajudantes.md` y ejecuta:

```bash
python3 semana.py rascunho
python3 semana.py gerar
```

Formato de `publicados.md` (una línea por publicación; se excluyen las que no tienen "publicado"):

```markdown
| Tema | Data | Estado |
|---|---|---|
| Aula: o primeiro agente | 05/11/2026 | publicado 05/11/2026 — https://exemplo.com/aula |
| Guia do backup | 06/11/2026 | em produção |
```

Solo usa la biblioteca estándar de Python 3 (no hace falta `pip install`). En Windows, cambia `python3` por `py`.

## Las siete secciones

1. **Lo único que hay que hacer esta semana** — una tarea que termina con 1 resultado funcionando (no "vi el video").
2. **Tu caso → tu camino** — tabla "usa X → mira Y".
3. **Victorias de la comunidad** — de `vitorias.md`: `- Nombre — qué hizo — enlace`.
4. **Lo que llegó** — se lee de las fuentes; solo lo que quedó dentro del período de la semana.
5. **Puedes ignorar** — de 2 a 4 novedades que pueden esperar, con el motivo.
6. **¿Te trabaste?** — dónde y cómo pedir ayuda (texto de ayuda en `config.json`).
7. **Quién ayudó más** — ranking manual de `ajudantes.md` (opcional; si está vacío, se muestra vacío).

## Fuentes de "Lo que llegó" (`config.json` › `fontes`)

| tipo | Qué lee | Campos |
|---|---|---|
| `tabela_md` | Tabla Markdown de publicaciones. Se incluye la fila cuyo estado empieza con la palabra de `so_com` (en INEMA, "publicad", que sirve para publicado y publicada; en inglés, "published"); la fecha es la que aparece después de esa palabra (dd/mm o dd/mm/aaaa) o, si falta, la de la columna de fecha. Las filas sin fecha se excluyen y se cuentan. | `caminho`, `coluna_titulo`, `coluna_data`, `coluna_estado`, `so_com`, `padrao_id_youtube` (opcional) |
| `git_log` | Commits de los repositorios listados, dentro del período de la semana (sin merges). | `repos`, `ignorar_prefixos`, `link_repo` |
| `feed` | Archivo guardado en el disco: JSON (`titulo`/`data`/`link`) o RSS/Atom. No se leen URL (el kit no usa la red). | `caminho` |

Cada fuente se activa o desactiva con `"ativo": true/false`.

## Telegram: límite de 4.096

El texto de Telegram se cuenta como lo hace Telegram (unidades UTF-16: cada emoji vale 2). Si supera 4.096, el kit lo divide en `telegram.md`, `telegram-2.md`… y corta preferentemente al inicio de una sección. La prueba `tests/test_semana.py` comprueba que ninguna parte supere el límite y que no se pierda nada.

## Ejemplo real: la semana de INEMA (01 a 08/11/2026)

En [`exemplos/2026-11-08/`](exemplos/2026-11-08/): `publicados.md` (copia limpia de la semana), `rascunho.md`, `telegram.md`, `email.html`, `pagina.html` e imágenes en 1440 px y 390 px. El kit viene configurado para INEMA (lee la tabla de producciones de video de INEMA); cambia `config.json` para tu comunidad.

- Tabla consultada (08/11/2026): 90 filas, 50 publicadas con fecha, **26 en la semana**.
- Lo único que hay que hacer: *Responde las 6 preguntas de la Escalera del Negocio con IA y elige UN negocio para empezar.*
- Telegram: 3.671 caracteres, 1 mensaje.
- Victorias del ejemplo: entregas del propio INEMA, marcadas "(ejemplo)". Ayudantes: vacío (el kit no inventa nombres).

Comandos usados:

```bash
python3 semana.py rascunho --de 2026-11-01 --ate 2026-11-08 --saida exemplos
python3 semana.py gerar    --de 2026-11-01 --ate 2026-11-08 --saida exemplos
```

## Archivos

| Archivo | Para qué |
|---|---|
| `semana.py` | el script (borrador y generar) |
| `config.json` | comunidad, enlace, texto de ayuda, fuentes (viene con INEMA, que lee la tabla interna de producciones) |
| `config.exemplo.json` | ejecuta el ejemplo en cualquier clon (lee `exemplos/2026-11-08/publicados.md`) |
| `config.modelo.json` | plantilla genérica para tu comunidad (lee `publicados.md`); cópiala sobre `config.json` |
| `vitorias.md`, `ajudantes.md` | lo que el moderador anota durante la semana |
| `edicao.md` | la elección de la semana (lo único, tu caso, puedes ignorar); la que viene en el kit es el ejemplo de INEMA |
| `prompts/escolher-a-unica-coisa.md` | instrucción lista para Claude Code o Codex |
| `tests/` | pruebas sin red (`python3 -m unittest discover -s tests`) |
| `exemplos/` | la edición real de INEMA |
| `guia/` | página de presentación y guía (PT/EN/ES) |

## Idioma

La publicación sale en portugués: los títulos de las secciones están en `semana.py` (`texto_telegram`, `html_pagina`, `html_email`). Tradúcelos allí si tu comunidad habla otro idioma. El `edicao.md` ya acepta títulos en español (`## Lo único`, `## Tu caso → tu camino`, `## Puedes ignorar`).

## Licencia

MIT. Hecho por [INEMA.CLUB](https://inema.club).