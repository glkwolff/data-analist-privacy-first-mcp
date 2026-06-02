"""Testes do loader multi-formato.

Cobre dispatch por extensão (CSV/Parquet/Excel/JSON), JSON-Lines como
fallback, erros estruturados (arquivo ausente, sem permissão, formato
desconhecido, dataset vazio).
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pandas as pd
import pytest

from agente_dados_mcp.loader import FORMATOS_SUPORTADOS, carregar


@pytest.fixture
def dados() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "categoria": ["a", "b", "a", "c", "b"],
            "valor": [10.5, 20.0, 15.5, 8.0, 12.5],
        }
    )


def _assert_carregou(df: pd.DataFrame | None, erro: str | None, esperado: pd.DataFrame) -> None:
    assert erro is None, f"erro inesperado: {erro}"
    assert df is not None
    assert list(df.columns) == list(esperado.columns)
    assert len(df) == len(esperado)


def test_csv(tmp_path: Path, dados: pd.DataFrame) -> None:
    caminho = tmp_path / "x.csv"
    dados.to_csv(caminho, index=False)
    df, erro = carregar(str(caminho))
    _assert_carregou(df, erro, dados)


def test_parquet(tmp_path: Path, dados: pd.DataFrame) -> None:
    caminho = tmp_path / "x.parquet"
    dados.to_parquet(caminho, index=False)
    df, erro = carregar(str(caminho))
    _assert_carregou(df, erro, dados)


def test_excel_xlsx(tmp_path: Path, dados: pd.DataFrame) -> None:
    caminho = tmp_path / "x.xlsx"
    dados.to_excel(caminho, index=False)
    df, erro = carregar(str(caminho))
    _assert_carregou(df, erro, dados)


def test_excel_multi_aba_le_a_primeira(tmp_path: Path, dados: pd.DataFrame) -> None:
    caminho = tmp_path / "multi.xlsx"
    outra = pd.DataFrame({"a": [99]})
    with pd.ExcelWriter(caminho) as writer:
        dados.to_excel(writer, sheet_name="primeira", index=False)
        outra.to_excel(writer, sheet_name="segunda", index=False)
    df, erro = carregar(str(caminho))
    assert erro is None
    assert df is not None
    # Carregamos só a primeira aba — colunas batem com `dados`, não com `outra`.
    assert list(df.columns) == list(dados.columns)


def test_json_array_de_registros(tmp_path: Path, dados: pd.DataFrame) -> None:
    caminho = tmp_path / "x.json"
    caminho.write_text(dados.to_json(orient="records"))
    df, erro = carregar(str(caminho))
    _assert_carregou(df, erro, dados)


def test_json_lines_fallback(tmp_path: Path, dados: pd.DataFrame) -> None:
    caminho = tmp_path / "x.json"
    linhas = [json.dumps(r) for r in dados.to_dict(orient="records")]
    caminho.write_text("\n".join(linhas))
    df, erro = carregar(str(caminho))
    _assert_carregou(df, erro, dados)


# ---------------------------------------------------------------------------
# Casos de erro estruturado
# ---------------------------------------------------------------------------


def test_arquivo_inexistente_retorna_erro(tmp_path: Path) -> None:
    df, erro = carregar(str(tmp_path / "nao_existe.csv"))
    assert df is None
    assert erro is not None
    assert "não encontrado" in erro.lower()


def test_caminho_aponta_pra_diretorio_falha(tmp_path: Path) -> None:
    df, erro = carregar(str(tmp_path))
    assert df is None
    assert erro is not None
    assert "regular" in erro.lower()


def test_formato_desconhecido_retorna_lista_de_suportados(tmp_path: Path) -> None:
    caminho = tmp_path / "x.tsv"
    caminho.write_text("a\tb\n1\t2\n")
    df, erro = carregar(str(caminho))
    assert df is None
    assert erro is not None
    assert "não suportado" in erro.lower()
    # Mensagem cita o que ESTÁ disponível pra que o LLM tenha alternativa.
    for nome in FORMATOS_SUPORTADOS.values():
        assert nome in erro


def test_arquivo_sem_extensao_e_rejeitado(tmp_path: Path) -> None:
    caminho = tmp_path / "dataset_sem_ext"
    caminho.write_text("a,b\n1,2\n")
    df, erro = carregar(str(caminho))
    assert df is None
    assert erro is not None
    assert "não suportado" in erro.lower()


def test_csv_vazio_retorna_erro(tmp_path: Path) -> None:
    caminho = tmp_path / "vazio.csv"
    caminho.write_text("a,b,c\n")
    df, erro = carregar(str(caminho))
    assert df is None
    assert erro is not None
    assert "linhas" in erro.lower()


def test_csv_malformado_retorna_erro_tipado(tmp_path: Path) -> None:
    caminho = tmp_path / "ruim.csv"
    # Mistura aspas inválidas que o parser não consegue resolver.
    caminho.write_text('a,b\n"sem fechar,2\n')
    df, erro = carregar(str(caminho))
    assert df is None
    assert erro is not None
    assert "csv" in erro.lower()


def test_sem_permissao_de_leitura(tmp_path: Path, dados: pd.DataFrame) -> None:
    caminho = tmp_path / "x.csv"
    dados.to_csv(caminho, index=False)
    # Tira permissão de leitura.
    os.chmod(caminho, 0)
    try:
        df, erro = carregar(str(caminho))
        # root ignora permissões — só rodamos a asserção quando o teste roda
        # como usuário comum.
        if os.geteuid() != 0:
            assert df is None
            assert erro is not None
            assert "permiss" in erro.lower()
    finally:
        os.chmod(caminho, stat.S_IRUSR | stat.S_IWUSR)
