"""Testes do semana.py — rodam sem rede e sem ler nada fora de tests/.

    python3 -m unittest discover -s tests -v
"""
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import semana  # noqa: E402

FIXTURE = AQUI / "fixtures" / "producoes.md"
FONTE = {"tipo": "tabela_md", "nome": "fixture", "caminho": str(FIXTURE), "coluna_titulo": "Tema",
         "coluna_data": "Dono", "coluna_estado": "Estado", "so_com": "publicad",
         "padrao_id_youtube": r"lives\d+\s+(?:16:9\s+|9:16\s+)?`?((?=[A-Za-z0-9_-]*[0-9A-Z_-])[A-Za-z0-9_-]{11})`?(?![A-Za-z0-9_-])"}
D = dt.date


class TestJanela(unittest.TestCase):
    def test_padrao_sao_7_dias_terminando_no_ate(self):
        jan = semana.janela(D(2026, 11, 8))
        self.assertEqual(jan, (D(2026, 11, 2), D(2026, 11, 8)))
        self.assertEqual((jan[1] - jan[0]).days + 1, 7)

    def test_bordas_entram_e_vizinhos_ficam_fora(self):
        jan = semana.janela(D(2026, 11, 8), 7)
        self.assertTrue(semana.na_janela(D(2026, 11, 2), jan))
        self.assertTrue(semana.na_janela(D(2026, 11, 8), jan))
        self.assertFalse(semana.na_janela(D(2026, 11, 1), jan))
        self.assertFalse(semana.na_janela(D(2026, 11, 9), jan))
        self.assertFalse(semana.na_janela(None, jan))

    def test_de_explicito_e_virada_de_mes(self):
        self.assertEqual(semana.janela(D(2026, 11, 8), de=D(2026, 11, 1)), (D(2026, 11, 1), D(2026, 11, 8)))
        self.assertEqual(semana.janela(D(2026, 11, 3))[0], D(2026, 10, 28))
        with self.assertRaises(ValueError):
            semana.janela(D(2026, 11, 1), de=D(2026, 11, 5))

    def test_tabela_respeita_a_janela(self):
        itens, _ = semana.ler_tabela_md(FIXTURE.read_text(encoding="utf-8"), FONTE)
        jan7 = semana.janela(D(2026, 11, 8))
        dentro = [x["titulo"] for x in itens if semana.na_janela(x["data"], jan7)]
        self.assertEqual(len(dentro), 6)
        self.assertFalse(any(t.startswith("Os 25 conceitos") for t in dentro))  # 01/11 fica fora em 7 dias
        jan8 = semana.janela(D(2026, 11, 8), de=D(2026, 11, 1))
        self.assertEqual(sum(semana.na_janela(x["data"], jan8) for x in itens), 7)


class TestTabela(unittest.TestCase):
    def setUp(self):
        self.itens, self.cont = semana.ler_tabela_md(FIXTURE.read_text(encoding="utf-8"), FONTE)
        self.por = {x["titulo"]: x for x in self.itens}

    def test_contagem(self):
        self.assertEqual(self.cont, {"linhas": 11, "acima_do_cabecalho": 1, "nao_publicadas": 2,
                                     "sem_data": 1, "publicadas": 8})

    def test_linha_acima_do_cabecalho_e_ignorada(self):
        self.assertFalse(any("Linha solta" in t for t in self.por))

    def test_data_de_publicado_vence_a_data_do_dono(self):
        self.assertEqual(self.por["Bolha da IA — o tombo de 5–6/11/2026"]["data"], D(2026, 11, 7))  # dono 06/11
        self.assertEqual(self.por["Prospecção B2B por sinais"]["data"], D(2026, 11, 4))  # dono 01/11

    def test_publicado_sem_data_usa_o_dono(self):
        self.assertEqual(self.por["Lance sua Startup — 50+ sites"]["data"], D(2026, 11, 7))

    def test_em_producao_e_pronto_nao_entram(self):
        self.assertNotIn("Agentes que se autoaprimoram", self.por)
        self.assertNotIn("Robô de IA para criança", self.por)

    def test_links(self):
        self.assertEqual(self.por["MovieFlow — filme de IA de graça"]["link"], "https://www.youtube.com/watch?v=0zyz-H-1qXQ")
        self.assertEqual(self.por["claude-diretor — mascote INEMA animado"]["link"], "https://www.youtube.com/watch?v=dc1A1sZbREc")
        # "explicativo" tem 11 letras mas não é id do YouTube
        vc = next(x for t, x in self.por.items() if t.startswith("video-codigo"))
        self.assertEqual(vc["link"], "")


class TestTelegram(unittest.TestCase):
    def test_u16_conta_emoji_como_2(self):
        self.assertEqual(semana.u16("abc"), 3)
        self.assertEqual(semana.u16("ção"), 3)
        self.assertEqual(semana.u16("🚀"), 2)

    def test_texto_curto_nao_divide(self):
        self.assertEqual(semana.dividir("1) A ÚNICA COISA\noi\n"), ["1) A ÚNICA COISA\noi\n"])

    def test_divide_em_ate_4096_sem_perder_nada(self):
        secoes = []
        for n in range(1, 8):
            corpo = "".join(f"• item {n}.{k} — 🚀 ação concreta com acentuação https://exemplo.org/{k}\n" for k in range(40))
            secoes.append(f"{n}) SEÇÃO {n}\n{corpo}\n")
        texto = "".join(secoes)
        self.assertGreater(semana.u16(texto), 4096 * 2)
        partes = semana.dividir(texto, 4096)
        self.assertGreater(len(partes), 2)
        self.assertEqual("".join(partes), texto)
        for p in partes:
            self.assertLessEqual(semana.u16(p), 4096)
        # o corte cai no início de uma seção quando a seção cabe inteira
        self.assertTrue(all(p.startswith(tuple(f"{n}) " for n in range(1, 8))) for p in partes))

    def test_linha_gigante_e_cortada(self):
        texto = "1) X\n" + ("ã" * 5000) + "🚀" * 10 + "\n"
        partes = semana.dividir(texto, 4096)
        self.assertEqual("".join(partes), texto)
        self.assertTrue(all(semana.u16(p) <= 4096 for p in partes))


class TestArquivosDoModerador(unittest.TestCase):
    def test_vitorias_e_ajudantes(self):
        v = semana.ler_vitorias("<!-- - Fulano — comentado — x -->\n- Ana — publicou o site — https://a.b/c\n- Beto — fez o backup\n")
        self.assertEqual([x["nome"] for x in v], ["Ana", "Beto"])
        self.assertEqual(v[0]["link"], "https://a.b/c")
        self.assertEqual(v[0]["feito"], "publicou o site")
        aj = semana.ler_ajudantes("- Caio — 3 respostas\n- Dora — 12 respostas — instalou o terminal de 3\n")
        self.assertEqual([x["nome"] for x in aj], ["Dora", "Caio"])

    def test_edicao(self):
        ed = semana.ler_edicao("## A única coisa\ntítulo: Rode X\npor que: porque sim\nresultado: X rodando\n"
                               "link: https://x.y/z\n\n## Seu caso → seu caminho\n| Você usa | Veja |\n|---|---|\n"
                               "| ChatGPT | [Guia](https://g.h/i) |\n\n## Pode ignorar\n- Notícia A — depois\n")
        self.assertEqual(ed["unica"]["titulo"], "Rode X")
        self.assertEqual(ed["unica"]["link"], "https://x.y/z")
        self.assertEqual(ed["caso"], [{"usa": "ChatGPT", "veja": "Guia", "link": "https://g.h/i"}])
        self.assertEqual(ed["ignorar"], ["Notícia A — depois"])


class TestPontaAPonta(unittest.TestCase):
    def test_gerar_monta_as_3_saidas_com_as_7_secoes(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copy(FIXTURE, tmp / "producoes.md")
            (tmp / "vitorias.md").write_text("- Ana — publicou o site — https://a.b/c\n", encoding="utf-8")
            (tmp / "edicao.md").write_text("## A única coisa\ntítulo: Rode X\nresultado: X rodando\nlink: https://x.y/z\n", encoding="utf-8")
            cfg = {"comunidade": "Teste", "link": "https://t.e", "fontes": [dict(FONTE, caminho="producoes.md")],
                   "plantao": {"texto": "Pergunte no grupo."}}
            (tmp / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
            r = semana.main(["gerar", "--config", str(tmp / "config.json"), "--ate", "2026-11-08"])
            self.assertEqual(r, 0)
            pasta = tmp / "saida" / "2026-11-08"
            tg = (pasta / "telegram.md").read_text(encoding="utf-8")
            self.assertLessEqual(semana.u16(tg), 4096)
            for n in range(1, 8):
                self.assertIn(f"{n}) ", tg)
            self.assertIn("O QUE CHEGOU (6 na semana)", tg)
            pag = (pasta / "pagina.html").read_text(encoding="utf-8")
            for ancora in ("unica", "caso", "vitorias", "chegou", "ignorar", "travou", "ajudou"):
                self.assertIn(f'id="{ancora}"', pag)
            self.assertIn("Rode X", (pasta / "email.html").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(tmp)

    def test_gerar_sem_unica_coisa_recusa(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "edicao.md").write_text("## A única coisa\n\n", encoding="utf-8")
            (tmp / "config.json").write_text(json.dumps({"fontes": []}), encoding="utf-8")
            self.assertEqual(semana.main(["gerar", "--config", str(tmp / "config.json"), "--ate", "2026-11-08"]), 2)
        finally:
            shutil.rmtree(tmp)

    @unittest.skipUnless(shutil.which("git"), "git ausente")
    def test_git_log_local(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                   "PATH": "/usr/bin:/bin"}
            run = lambda *a, data: subprocess.run(["git", "-C", str(tmp), *a], check=True, capture_output=True,
                                                  env=dict(env, GIT_AUTHOR_DATE=data, GIT_COMMITTER_DATE=data))
            run("init", "-q", data="2026-11-05T10:00:00")
            for dia, msg in (("2026-10-20", "antigo"), ("2026-11-05", "guia novo"), ("2026-11-06", "handoff: x")):
                (tmp / f"{dia}.txt").write_text(dia)
                run("add", ".", data=f"{dia}T10:00:00")
                run("commit", "-qm", msg, data=f"{dia}T10:00:00")
            itens = semana.ler_git_log({"repos": [str(tmp)], "ignorar_prefixos": ["handoff:"]},
                                       semana.janela(D(2026, 11, 8)), tmp)
            self.assertEqual([x["titulo"].split(": ", 1)[1] for x in itens], ["guia novo"])
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
