"""Smoke test end-to-end: simula um cliente MCP chamando as 4 tools em sequência.

Não usa o protocolo MCP stdio real (isso é responsabilidade do FastMCP).
Chama as funções decoradas diretamente, validando o pipeline completo:
carregar → autorizar → executar → limpar.
"""

from __future__ import annotations

import os

import pytest

from agente_dados_mcp.server import (
    autorizar_colunas,
    carregar_dataset,
    executar_analise,
    limpar_sessao,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADULT_CSV = os.path.join(REPO_ROOT, "exemplos", "adult.csv")


pytestmark = pytest.mark.skipif(
    not os.path.exists(ADULT_CSV),
    reason="exemplos/adult.csv não está disponível",
)


def test_fluxo_completo_adult():
    limpar_sessao()

    # 1. carregar
    schema = carregar_dataset(ADULT_CSV)
    assert schema["ok"] is True
    assert schema["total_linhas"] > 30000

    # PII obrigatórias detectadas no dataset Adult
    for esperada in ("age", "race", "sex", "native-country", "income"):
        assert esperada in schema["colunas_pii"], (
            f"{esperada} deveria estar em colunas_pii"
        )

    # Schema NÃO contém valores
    payload = str(schema)
    for valor_proibido in ("United-States", "Bachelors", "Self-emp-not-inc"):
        assert valor_proibido not in payload

    # 2. autorizar
    autorizadas = ["age", "workclass", "education", "hours-per-week", "income"]
    auth = autorizar_colunas(autorizadas)
    assert auth["ok"] is True
    assert set(auth["autorizadas"]) == set(autorizadas)

    # 3. executar análise legítima
    codigo = (
        "import plotly.express as px\n"
        "resumo = df.groupby('education')['hours-per-week'].mean().reset_index()\n"
        "resumo = resumo.sort_values('hours-per-week', ascending=False)\n"
        "fig = px.bar(resumo, x='education', y='hours-per-week', "
        "title='Horas semanais médias por escolaridade')\n"
    )
    result = executar_analise(codigo=codigo, descricao="horas por escolaridade")
    # Deve retornar 3 blocos: image + text resumo + text link
    assert len(result) == 3
    assert result[0].type == "image"
    assert result[0].mimeType == "image/png"
    assert result[1].type == "text"
    assert "Horas semanais" in result[1].text or "horas" in result[1].text.lower()
    assert result[2].type == "text"
    assert "interativa" in result[2].text.lower() or "html" in result[2].text.lower()

    # 4. tentativa de injeção
    bloqueado = executar_analise(
        codigo="import os\nfig = os.listdir('/')",
        descricao="tentativa de injeção",
    )
    assert len(bloqueado) == 1
    assert bloqueado[0].type == "text"
    assert "BLOQUEADO" in bloqueado[0].text

    # 5. limpar
    cleanup = limpar_sessao()
    assert cleanup["ok"] is True

    # após limpar, executar deve falhar
    apos_limpar = executar_analise(codigo="fig = px.bar(df, x='a')", descricao="x")
    assert "nenhum dataset" in apos_limpar[0].text.lower()
