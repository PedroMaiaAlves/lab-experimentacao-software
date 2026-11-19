import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experimento import plano, poder  # noqa: E402


def test_plano_balanceado_e_completo():
    execs = plano.gerar_plano("E1")
    assert len(execs) == 4 * plano.EXECUCOES_POR_CELULA
    contagem = Counter((e.broker, e.tamanho_bytes) for e in execs)
    assert set(contagem.values()) == {plano.EXECUCOES_POR_CELULA}
    assert len({e.id_execucao for e in execs}) == len(execs)
    assert [e.ordem for e in execs] == list(range(1, len(execs) + 1))


def test_plano_reprodutivel_e_aleatorio():
    assert plano.gerar_plano("E1") == plano.gerar_plano("E1")
    e1 = [e.id_execucao.removeprefix("E1-") for e in plano.gerar_plano("E1")]
    e2 = [e.id_execucao.removeprefix("E2-") for e in plano.gerar_plano("E2")]
    assert e1 != e2  # E1 e E2 têm ordens diferentes
    sequencial = sorted(e1)
    assert e1 != sequencial  # não está em ordem de célula


def test_versoes_da_proposta():
    execs = plano.gerar_plano("E2")
    assert {(e.broker, e.versao) for e in execs} == {("kafka", "4.4.0"), ("rabbitmq", "4.4.1")}


@pytest.mark.parametrize("exp,n", [("E3", 10), ("E1", 1)])
def test_entradas_invalidas(exp, n):
    with pytest.raises(ValueError):
        plano.gerar_plano(exp, n)


def test_salvar_plano(tmp_path):
    destino = plano.salvar_plano(plano.gerar_plano("E1", 3), tmp_path / "p.csv")
    linhas = destino.read_text(encoding="utf-8").splitlines()
    assert linhas[0].startswith("ordem,id_execucao,experimento,broker")
    assert len(linhas) == 1 + 12


def test_poder_sob_h0_controla_alfa():
    p = poder.poder(10, 1.0, 0.10, alfa=0.05, repeticoes=4000)
    assert 0.03 < p["welch_log"] < 0.07
    assert p["mann_whitney"] <= 0.07


def test_poder_cresce_com_n_e_efeito():
    pequeno = poder.poder(5, 1.10, 0.10)["welch_log"]
    grande_n = poder.poder(20, 1.10, 0.10)["welch_log"]
    grande_r = poder.poder(5, 1.50, 0.10)["welch_log"]
    assert grande_n > pequeno and grande_r > pequeno
