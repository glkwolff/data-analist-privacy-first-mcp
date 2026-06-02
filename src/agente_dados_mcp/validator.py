"""Validação AST do código gerado pelo LLM.

DEFESA EM PROFUNDIDADE: as tool descriptions instruem o LLM a não gerar
código perigoso, mas este módulo é a barreira automática que SEMPRE roda
antes da execução. Se uma camada falhar, esta segura.

Ver CLAUDE.md seção 9 — esta implementação deve cobrir os test cases
listados em tests/test_validator.py.
"""

from __future__ import annotations

import ast

BIBLIOTECAS_PERMITIDAS = {
    "pandas",
    "numpy",
    "plotly",
    "plotly.express",
    "plotly.graph_objects",
    "plotly.io",
    "plotly.subplots",
    "agente_dados_mcp",
    "agente_dados_mcp.theme",
}

FUNCOES_PROIBIDAS = {
    "eval", "exec", "compile", "__import__", "open",
    "globals", "locals", "vars", "getattr", "setattr",
    "delattr", "input", "help", "breakpoint",
}

MODULOS_PROIBIDOS = {
    "os", "sys", "subprocess", "socket", "urllib", "urllib.request",
    "requests", "http", "pathlib", "shutil", "pickle", "marshal",
    "importlib", "ctypes", "multiprocessing", "threading",
    "builtins", "__builtin__",
}

DUNDERS_PERMITIDOS = {"__name__", "__doc__"}


def validar_codigo(codigo: str) -> tuple[bool, str]:
    """Retorna (ok, mensagem).

    ok=False => código DEVE ser bloqueado. Mensagem é segura pra mostrar ao
    LLM (não expõe internals).
    """
    try:
        arvore = ast.parse(codigo)
    except SyntaxError as e:
        return False, f"Código não é Python válido: {e.msg} (linha {e.lineno})"

    for node in ast.walk(arvore):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if alias.name in MODULOS_PROIBIDOS or base in MODULOS_PROIBIDOS:
                    return False, f"Módulo proibido: {alias.name}"
                if base not in BIBLIOTECAS_PERMITIDAS and alias.name not in BIBLIOTECAS_PERMITIDAS:
                    return False, f"Biblioteca não permitida: {alias.name}"

        if isinstance(node, ast.ImportFrom):
            modulo = node.module or ""
            base = modulo.split(".")[0] if modulo else ""
            if modulo in MODULOS_PROIBIDOS or base in MODULOS_PROIBIDOS:
                return False, f"Módulo proibido: {modulo}"
            if modulo and base not in BIBLIOTECAS_PERMITIDAS and modulo not in BIBLIOTECAS_PERMITIDAS:
                return False, f"Biblioteca não permitida: {modulo}"

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FUNCOES_PROIBIDAS:
                return False, f"Função proibida: {node.func.id}()"

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__"):
                if node.attr not in DUNDERS_PERMITIDOS:
                    return False, f"Atributo dunder proibido: .{node.attr}"

        if isinstance(node, ast.Name) and node.id in FUNCOES_PROIBIDAS:
            if not isinstance(node.ctx, ast.Store):
                return False, f"Referência a função proibida: {node.id}"

    return True, "OK"
