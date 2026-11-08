# semana-inema — la semana sin sobrecarga

[![semana-inema](guia/assets/banner-es.jpg)](https://inematds.github.io/semana-inema/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

semana-inema es un kit gratuito para quienes cuidan una comunidad (grupo de Telegram, WhatsApp, clase o lista de correo). Cada semana lee las novedades de tus fuentes y arma una edición breve con siete partes: lo único que hay que hacer, el camino para cada caso, los logros de los miembros, lo que llegó, lo que puedes ignorar, dónde pedir ayuda y quién más ayudó. Se entrega en tres formatos: mensaje de Telegram, correo electrónico y página. Solo necesitas Python en tu computadora; nada se publica automáticamente.

> Tu comunidad no necesita más contenido. Necesita saber qué hacer.

## 📖 Guía de uso

Guía completa (el método + paso a paso): **https://inematds.github.io/semana-inema/guia/es/**

## El proceso, de principio a fin

Quién hace qué: 🧠 el moderador (tú) · ⚙️ el script · 🤖 un agente (Claude Code o Codex), opcional.

| # | Paso | Comando / archivo | Quién |
|---|---|---|---|
| 1 | Configurar una vez: nombre, enlace, texto de ayuda y fuentes | `config.json` | 🧠 |
| 2 | Durante la semana, anotar los logros y quién ayudó (con el permiso de las personas) | `vitorias.md`, `ajudantes.md` | 🧠 |
| 3 | Reunir lo que llegó durante la semana y armar el borrador | `python3 semana.py rascunho` → `saida/<data>/rascunho.md` | ⚙️ |
| 4 | Elegir lo único que hay que hacer, la tabla «tu caso → tu camino» y lo que «puedes ignorar» | pegar `prompts/escolher-a-unica-coisa.md` → escribe `edicao.md` | 🤖 (o 🧠 a mano) |
| 5 | Leer y ajustar la elección | `edicao.md` | 🧠 |
| 6 | Generar los tres formatos | `python3 semana.py gerar` → `telegram.md` (+ `telegram-2.md`…), `email.html`, `pagina.html` | ⚙️ |
| 7 | Revisar y publicar (el kit no envía nada) | pegar en el grupo, en el correo, en el sitio | 🧠 |

Si la semana no termina hoy, indica las fechas en los pasos 3 y 6: `--ate AAAA-MM-DD` (último día) y, si quieres, `--de AAAA-MM-DD`. Sin `--de`, el período abarca 7 días y termina en `--ate`.

## Empezar

```bash
git clone https://github.com/inematds/semana-inema.git
cd semana-inema
python3 -m unittest discover -s tests      # tiene que terminar con OK
python3 semana.py rascunho
python3 semana.py gerar
```

Solo usa la biblioteca estándar de Python 3 (no hace falta `pip install`). En Windows, cambia `python3` por `py`.

## Las siete secciones

1. **Lo único de esta semana** — una tarea que termina con 1 resultado funcionando (no «vi el video»).
2. **Tu caso → tu camino** — tabla «usa X → consulta Y».
3. **Logros de la comunidad** — de `vitorias.md`: `- Nombre — qué hizo — enlace`.
4. **Lo que llegó** — leído de las fuentes, solo lo que entró en el período de la semana.
5. **Puedes ignorar** — de 2 a 4 novedades que pueden esperar, con el motivo.
6. **¿Te trabaste?** — dónde y cómo pedir ayuda (el texto de el texto de ayuda está en `config.json`).
7. **Quién más ayudó** — clasificación manual de `ajudantes.md` (opcional; si está vacío, aparece vacío).

## Fuentes de «Lo que llegó» (`config.json` › `fontes`)

| tipo | Qué lee | Campos |
|---|---|---|
| `tabela_md` | Tabla Markdown de publicaciones. Se incluye la fila cuyo estado empieza con la palabra de `so_com` (en INEMA, «publicad», que vale para publicado y publicada); la fecha es la que aparece después de esa palabra (dd/mm o dd/mm/aaaa) o, si falta, la de la columna de fecha. Se excluyen las filas sin fecha y se cuentan. | `caminho`, `coluna_titulo`, `coluna_data`, `coluna_estado`, `so_com`, `padrao_id_youtube` (opcional) |
| `git_log` | Commits de los repositorios indicados, durante el período de la semana (sin merges). | `repos`, `ignorar_prefixos`, `link_repo` |
| `feed` | Archivo guardado en el disco: JSON (`titulo`/`data`/`link`) o RSS/Atom. No se lee la URL (el kit no usa la red). | `caminho` |

Cada fuente se activa o desactiva con `"ativo": true/false`.

En INEMA, la palabra usada para `so_com` es `publicad` en portugués; en español (ES, América Latina, «tú»), también se usa, por ejemplo, `publicad`.

## Telegram: límite de 4.096

El texto de Telegram se cuenta como lo hace Telegram (unidades UTF-16: cada emoji vale 2). Si supera los 4.096, el kit lo divide en `telegram.md`, `telegram-2.md`… y corta de preferencia al inicio de una sección. La prueba `tests/test_semana.py` comprueba que ninguna parte supere el límite y que no se pierda nada.

## Ejemplo real: la semana de INEMA (del 01 al 08/11/2026)

En [`exemplos/2026-11-08/`](exemplos/2026-11-08/): `rascunho.md`, `telegram.md`, `email.html`, `pagina.html` y capturas de pantalla en 1440 px y 390 px. El kit viene configurado para INEMA (lee la tabla de producciones de video de INEMA); cambia `config.json` para adaptarlo a tu comunidad.

- Tabla leída (08/11/2026): 90 filas, 50 publicadas con fecha, **26 en la semana**.
- Lo único: *Responde las 6 preguntas de la Escalera del Negocio con IA y elige UN negocio para empezar.* (en portugués en el ejemplo)
- Telegram: 3.671 caracteres, 1 mensaje.
- Logros del ejemplo: entregas del propio INEMA, marcadas como «(exemplo)». Ayudantes: vacío (el kit no inventa nombres).

Comandos usados:

```bash
python3 semana.py rascunho --de 2026-11-01 --ate 2026-11-08 --saida exemplos
python3 semana.py gerar    --de 2026-11-01 --ate 2026-11-08 --saida exemplos
```

## Archivos

| Archivo | Para qué |
|---|---|
| `semana.py` | el script (rascunho y gerar) |
| `config.json` | comunidad, enlace, texto de ayuda, fuentes (viene con INEMA) |
| `vitorias.md`, `ajudantes.md` | lo que el moderador anota durante la semana |
| `edicao.md` | la elección de la semana (lo único, tu caso, puedes ignorar) |
| `prompts/escolher-a-unica-coisa.md` | pedido listo para Claude Code o Codex |
| `tests/` | pruebas sin red (`python3 -m unittest discover -s tests`) |
| `exemplos/` | la edición real de INEMA |
| `guia/` | página de presentación y guía (PT/EN/ES) |

## Licencia

MIT. Hecho por [INEMA.CLUB](https://inema.club).