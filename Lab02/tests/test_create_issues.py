from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock


LAB02_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = LAB02_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import create_issues  # noqa: E402


class CreateIssuesPreviewTest(unittest.TestCase):
    def setUp(self):
        self.protocol = create_issues.load_protocol(LAB02_ROOT / "protocol.json")
        self.issues = create_issues.build_issues(self.protocol)

    def test_gera_exatamente_doze_issues_com_titulos_unicos(self):
        self.assertEqual(12, len(self.issues))
        self.assertEqual(12, len({issue["title"] for issue in self.issues}))

    def test_usa_participantes_e_atribuicoes_do_protocolo(self):
        primeira = self.issues[0]
        ultima = self.issues[-1]
        self.assertEqual("PedroMaiaAlves", primeira["assignee"])
        self.assertIn("[Pedro][01] Consolidar Janelas — IA", primeira["title"])
        self.assertEqual("LorranX", ultima["assignee"])
        self.assertIn("[Lorran][04] Planejar Recargas — IA", ultima["title"])

    def test_corpo_registra_configuracao_e_evidencias_do_trial(self):
        body = self.issues[5]["body"]
        self.assertIn("Participante: Diogo (`diogo`)", body)
        self.assertIn("Kata: Agrupar Alertas (`kata03`)", body)
        self.assertIn("Tratamento: IA", body)
        self.assertIn("Ordem do participante: 2", body)
        self.assertIn("## Evidências", body)

    def test_previa_exibe_todas_as_issues_sem_publicar(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), mock.patch.object(
            create_issues, "publish_issues"
        ) as publish:
            create_issues.main(["--protocol", str(LAB02_ROOT / "protocol.json")])
        publish.assert_not_called()
        self.assertEqual(12, output.getvalue().count("[PRÉVIA]"))
        self.assertIn("nada foi publicado", output.getvalue())

    def test_previa_nao_consulta_o_github(self):
        with mock.patch.object(create_issues.subprocess, "run") as run:
            create_issues.print_preview(self.issues)
        run.assert_not_called()

    def test_publicacao_ignora_titulo_ja_existente(self):
        issue = self.issues[0]
        output = io.StringIO()
        with contextlib.redirect_stdout(output), mock.patch.object(
            create_issues, "existing_titles", return_value={issue["title"]}
        ), mock.patch.object(create_issues.subprocess, "run") as run:
            create_issues.publish_issues([issue])
        run.assert_not_called()
        self.assertIn("1 ignoradas", output.getvalue())


if __name__ == "__main__":
    unittest.main()
