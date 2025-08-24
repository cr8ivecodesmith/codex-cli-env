import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import types
import pytest


@pytest.fixture(scope="session")
def codexenv_path() -> Path:
    return Path(__file__).resolve().parents[1] / "bin" / "codexenv"


@pytest.fixture()
def codexenv_mod(codexenv_path: Path) -> types.ModuleType:
    loader = SourceFileLoader("codexenv_mod", str(codexenv_path))
    spec = importlib.util.spec_from_loader("codexenv_mod", loader)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[arg-type]
    return mod


@pytest.fixture()
def temp_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, codexenv_mod):
    root = tmp_path / ".root"
    codex_home = tmp_path / ".codex_home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setenv("CODEXENV_ROOT", str(root))
    monkeypatch.setenv("CODEXENV_CODEX_HOME", str(codex_home))
    monkeypatch.chdir(work)
    # Return Paths constructed after env vars are set
    p = codexenv_mod.Paths()
    return p
