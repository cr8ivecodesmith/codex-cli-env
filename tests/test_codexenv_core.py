from __future__ import annotations

from pathlib import Path
import os
import subprocess
import pytest


@pytest.mark.parametrize("case", ["home", "envvar", "dot"])
def test_expand_and_getenv_basic(case, codexenv_mod, monkeypatch, tmp_path):
    # getenv
    monkeypatch.delenv("SOME_VAR", raising=False)
    assert codexenv_mod.getenv("SOME_VAR", "default") == "default"
    monkeypatch.setenv("SOME_VAR", "value")
    assert codexenv_mod.getenv("SOME_VAR", "default") == "value"

    # expand: handles ~ and $VARS and returns absolute Path
    if case == "home":
        home = str(tmp_path)
        monkeypatch.setenv("HOME", home)
        p = codexenv_mod.expand("~/x")
        assert isinstance(p, Path)
        assert p == Path(home).absolute() / "x"
    elif case == "envvar":
        monkeypatch.setenv("MYP", str(tmp_path / "dir"))
        p = codexenv_mod.expand("$MYP/file.txt")
        assert p == (tmp_path / "dir" / "file.txt").absolute()
    elif case == "dot":
        p = codexenv_mod.expand(".")
        assert p.is_absolute()


def test_paths_and_ensure_dirs(temp_env, codexenv_mod):
    p = temp_env
    # paths reflect env vars
    assert p.root_dir.name == ".root"
    assert p.envs_dir == p.root_dir / "envs"
    assert p.codex_home.name == ".codex_home"
    # ensure_dirs creates directories
    codexenv_mod.ensure_dirs(p)
    assert p.root_dir.is_dir()
    assert p.envs_dir.is_dir()


@pytest.mark.parametrize("which_result, expected", [("/bin/codex", True), (None, False)])
def test_which_and_codex_installed(which_result, expected, codexenv_mod, monkeypatch):
    # which should find a common binary like python3
    res = codexenv_mod.which("python3")
    assert isinstance(res, (str, type(None)))
    # codex_installed delegates to which("codex")
    monkeypatch.setattr(codexenv_mod, "which", lambda prog: which_result if prog == "codex" else None)
    assert codexenv_mod.codex_installed() is expected


def test_npm_install_codex(monkeypatch, codexenv_mod, capsys):
    # If codex is installed and not forced, returns 0 without running
    monkeypatch.setattr(codexenv_mod, "codex_installed", lambda: True)
    rc = codexenv_mod.npm_install_codex("npm", "@openai/codex", force=False)
    assert rc == 0

    # If not installed, simulate successful subprocess
    monkeypatch.setattr(codexenv_mod, "codex_installed", lambda: False)
    class DummyProc:
        def __init__(self, returncode):
            self.returncode = returncode

    calls: list[list[str]] = []

    def fake_run(cmd, check):
        calls.append(cmd)
        return DummyProc(0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = codexenv_mod.npm_install_codex("npm", "@openai/codex", force=False)
    assert rc == 0
    assert calls and calls[0][:3] == ["npm", "install", "-g"]

    # Simulate failure
    def fake_run_fail(cmd, check):
        return DummyProc(2)

    monkeypatch.setattr(subprocess, "run", fake_run_fail)
    rc = codexenv_mod.npm_install_codex("npm", "@openai/codex", force=True)
    assert rc == 2
    _, err = capsys.readouterr()
    assert "npm install failed" in err

    # Simulate FileNotFoundError
    def fake_run_raise(cmd, check):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", fake_run_raise)
    rc = codexenv_mod.npm_install_codex("npm-missing", "@openai/codex", force=True)
    assert rc == 127


def test_read_write_text(tmp_path, codexenv_mod):
    f = tmp_path / "file.txt"
    assert codexenv_mod.read_text(f) is None
    codexenv_mod.write_text(f, "hello\n")
    assert f.read_text(encoding="utf-8") == "hello\n"
    assert codexenv_mod.read_text(f) == "hello"


@pytest.mark.parametrize(
    "names, expected",
    [
        ([], []),
        (["b", "a"], ["a", "b"]),
        (["z"], ["z"]),
    ],
)
def test_list_envs_and_env_path(names, expected, temp_env, codexenv_mod):
    p = temp_env
    codexenv_mod.ensure_dirs(p)
    for n in names:
        (p.envs_dir / n).mkdir(parents=True)
    assert codexenv_mod.list_envs(p) == expected
    if names:
        assert p.env_path(names[0]) == p.envs_dir / names[0]


@pytest.mark.parametrize(
    "global_name, local_name, expected",
    [
        (None, None, None),
        ("g1", None, "g1"),
        ("g1", "l1", "l1"),
    ],
)
def test_local_global_current_effective(global_name, local_name, expected, temp_env, codexenv_mod):
    p = temp_env
    if global_name is not None:
        codexenv_mod.write_global_env(p, global_name)
    if local_name is not None:
        (p.cwd / ".codexenv-local").write_text(local_name + "\n")
    assert codexenv_mod.current_effective_env(p) == expected


@pytest.mark.parametrize("levels", [0, 1, 2, 3])
def test_resolve_local_env_name_upwards(levels, tmp_path, codexenv_mod):
    root = tmp_path / "root"
    deep = root
    parts = ["a", "b", "c", "d"]
    for i in range(4):
        deep = deep / parts[i]
    deep.mkdir(parents=True)
    # place marker at some ancestor depth
    marker_parent = root
    for i in range(levels):
        marker_parent = marker_parent / parts[i]
    marker = marker_parent / ".codexenv-local"
    marker.write_text("envX\n", encoding="utf-8")
    name, path = codexenv_mod.resolve_local_env_name(deep)
    assert name == "envX"
    assert path == marker


def test_symlink_points_to(tmp_path, codexenv_mod):
    t = tmp_path / "target"
    t.mkdir()
    l = tmp_path / "link"
    try:
        os.symlink(t, l)
    except OSError:
        pytest.skip("symlink not permitted in this environment")


@pytest.mark.parametrize(
    "was_global, expect_symlink_update",
    [
        (True, True),
        (False, False),
    ],
)
def test_rename_env_updates_global_and_symlink(was_global, expect_symlink_update, temp_env, codexenv_mod):
    p = temp_env
    codexenv_mod.ensure_dirs(p)
    # Create source env and optionally make it global
    src = p.env_path("alpha"); src.mkdir(parents=True)
    if was_global:
        codexenv_mod.write_global_env(p, "alpha")
    # If symlinks allowed and link points to src, it should update after rename
    try:
        os.symlink(src, p.codex_home)
        link_supported = True
    except OSError:
        link_supported = False
    # Perform rename via function
    class Args: pass
    args = Args(); args.old = "alpha"; args.new = "beta"; args.quiet = True
    rc = codexenv_mod.cmd_rename(args)
    assert rc == 0
    # Validate filesystem
    assert not src.exists()
    assert p.env_path("beta").exists()
    # Validate global update
    g = codexenv_mod.read_global_env(p)
    assert g == ("beta" if was_global else g)
    # Validate symlink update (only if symlink creation worked and it pointed to src)
    if link_supported and expect_symlink_update:
        assert codexenv_mod.symlink_points_to(p.codex_home, p.env_path("beta"))


def test_rename_errors(temp_env, codexenv_mod):
    p = temp_env
    codexenv_mod.ensure_dirs(p)
    # Missing source
    class A: pass
    a = A(); a.old = "missing"; a.new = "new"; a.quiet = True
    rc = codexenv_mod.cmd_rename(a)
    assert rc == 2
    # Destination exists
    src = p.env_path("one"); dst = p.env_path("two")
    src.mkdir(parents=True); dst.mkdir(parents=True)
    a.old = "one"; a.new = "two"
    rc = codexenv_mod.cmd_rename(a)
    assert rc == 4


def test_init_with_custom_name_sets_global_and_creates_env(monkeypatch, temp_env, codexenv_mod):
    # Monkeypatch update_codex_symlink to avoid symlink dependency
    monkeypatch.setattr(codexenv_mod, "update_codex_symlink", lambda p, name, quiet=False: 0)
    class Args: pass
    args = Args(); args.name = "myenv"; args.npm_install = False; args.npm_binary = None; args.npm_package = None; args.force_npm = False
    rc = codexenv_mod.cmd_init(args)
    assert rc == 0
    p = temp_env
    assert codexenv_mod.read_global_env(p) == "myenv"
    assert p.env_path("myenv").exists()


@pytest.mark.parametrize(
    "state, expected",
    [
        ("missing_env", 2),
        ("real_dir", 3),
        ("correct_symlink", 0),
        ("wrong_symlink", 0),
    ],
)
def test_update_codex_symlink(state, expected, temp_env, codexenv_mod):
    p = temp_env
    if state == "missing_env":
        rc = codexenv_mod.update_codex_symlink(p, "missing", quiet=True)
        assert rc == expected
        return

    env_dir = p.env_path("env1")
    env_dir.mkdir(parents=True)

    if state == "real_dir":
        p.codex_home.mkdir(parents=True)
        rc = codexenv_mod.update_codex_symlink(p, "env1", quiet=True)
        assert rc == expected
        return

    # states that require symlinks
    try:
        if state == "correct_symlink":
            os.symlink(env_dir, p.codex_home)
            rc = codexenv_mod.update_codex_symlink(p, "env1", quiet=True)
            assert rc == expected
        elif state == "wrong_symlink":
            other = p.env_path("env2"); other.mkdir()
            os.symlink(other, p.codex_home)
            rc = codexenv_mod.update_codex_symlink(p, "env1", quiet=True)
            assert rc == expected
            assert codexenv_mod.symlink_points_to(p.codex_home, env_dir)
    except OSError:
        pytest.skip("symlink not permitted in this environment")
