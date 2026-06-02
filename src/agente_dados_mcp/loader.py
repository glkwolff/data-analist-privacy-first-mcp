"""Carregamento de dataset por extensão.

Mantém a porta de entrada estreita: o servidor (`server.py`) só chama
`carregar(caminho)` e recebe (df, erro). Toda decisão de "qual parser
do pandas usar" mora aqui, então adicionar um formato novo no futuro
é um caso a mais no dispatch — sem mudar server/state/schema.

Privacy invariant: nenhuma função aqui loga conteúdo de células.
Mensagens de erro citam tipo da exceção e nome do arquivo, nada do
payload.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


FORMATOS_SUPORTADOS: dict[str, str] = {
    ".csv": "CSV",
    ".parquet": "Parquet",
    ".xlsx": "Excel",
    ".xls": "Excel",
    ".json": "JSON",
}


def formatos_legivel() -> str:
    """Lista canônica usada em mensagens de erro e na tool description."""
    return ", ".join(sorted(set(FORMATOS_SUPORTADOS.values())))


def _ler_csv(caminho: str) -> pd.DataFrame:
    import pandas as pd

    return pd.read_csv(caminho)


def _ler_parquet(caminho: str) -> pd.DataFrame:
    import pandas as pd

    return pd.read_parquet(caminho)


def _ler_excel(caminho: str) -> pd.DataFrame:
    import pandas as pd

    return pd.read_excel(caminho, sheet_name=0)


def _ler_json(caminho: str) -> pd.DataFrame:
    """Tenta o orient mais comum (array de registros) e cai pra `lines=True`
    se for JSON-Lines / NDJSON.
    """
    import pandas as pd

    try:
        return pd.read_json(caminho)
    except ValueError:
        return pd.read_json(caminho, lines=True)


_DISPATCH = {
    ".csv": _ler_csv,
    ".parquet": _ler_parquet,
    ".xlsx": _ler_excel,
    ".xls": _ler_excel,
    ".json": _ler_json,
}


def carregar(caminho: str) -> tuple[pd.DataFrame | None, str | None]:
    """Retorna (df, None) em sucesso, (None, mensagem) em falha.

    Erros possíveis:
      - arquivo não existe
      - sem permissão de leitura
      - extensão não suportada
      - falha do parser (CSV malformado, Parquet corrompido, etc.)
      - dependência opcional faltando (pyarrow / openpyxl)
      - dataset vazio (zero linhas)
    """
    if not os.path.exists(caminho):
        return None, f"Arquivo não encontrado: {caminho}"

    if not os.path.isfile(caminho):
        return None, f"Caminho não é um arquivo regular: {caminho}"

    if not os.access(caminho, os.R_OK):
        return None, f"Sem permissão de leitura: {caminho}"

    ext = os.path.splitext(caminho)[1].lower()
    if ext not in _DISPATCH:
        return None, (
            f"Formato não suportado: {ext or '(sem extensão)'}. "
            f"Suportados: {formatos_legivel()}."
        )

    try:
        df = _DISPATCH[ext](caminho)
    except ImportError as e:
        # pyarrow / openpyxl ausentes vêm como ImportError dentro do pandas.
        pacote = "pyarrow" if ext == ".parquet" else "openpyxl"
        return None, (
            f"Dependência ausente para {FORMATOS_SUPORTADOS[ext]}: "
            f"{pacote}. Reinstale com `pip install -e .` (ou inclua o "
            f"extra correspondente). Detalhe: {e}"
        )
    except Exception as e:  # noqa: BLE001
        return None, (
            f"Falha ao ler {FORMATOS_SUPORTADOS[ext]}: "
            f"{type(e).__name__}: {e}"
        )

    if df is None or df.empty:
        return None, "Arquivo carregado, mas não tem linhas."

    return df, None
