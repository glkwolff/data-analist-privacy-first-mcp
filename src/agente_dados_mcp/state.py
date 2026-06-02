"""Estado da sessão MCP.

Em memória do processo. Sessão morre quando o cliente fecha — by design,
ver CLAUDE.md seção 2. Não persistir entre conexões.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class SessionState:
    df: pd.DataFrame | None = None
    caminho_atual: str | None = None
    colunas_pii: list[str] = field(default_factory=list)
    colunas_autorizadas: list[str] = field(default_factory=list)
    schema_cache: dict | None = None

    def reset(self) -> None:
        self.df = None
        self.caminho_atual = None
        self.colunas_pii = []
        self.colunas_autorizadas = []
        self.schema_cache = None

    @property
    def carregado(self) -> bool:
        return self.df is not None


SESSION = SessionState()
