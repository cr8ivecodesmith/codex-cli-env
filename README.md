# Codex CLI Environments (codexenv)

Manage per-project Codex CLI accounts by switching `~/.codex` to named environments stored under `~/.codex-cli-env/envs/<name>`.

## Install

- Clone this repo (ideally to `~/.codex-cli-env`).
- Ensure the `bin/` directory is on your `PATH`.
- Optionally enable shell integration so the correct env applies as you `cd`.

Quick setup:

**Clone into home (or move the folder there)**

```
git clone https://github.com/cr8ivecodesmith/codex-cli-env.git ~/.codex-cli-env
```

**Add to PATH**
  - Bash:
    ```
    export PATH="$HOME/.codex-cli-env/bin:$PATH"
    ```
    or
    ```
    echo 'export PATH="$HOME/.codex-cli-env/bin:$PATH' >> ~/.bashrc
    ```
  - Fish:
    ```
    set PATH $HOME/.codex-cli-env/bin $PATH
    ```
    or
    ```
    echo 'set PATH $HOME/.codex-cli-env/bin $PATH' >> ~/.config/fish/config.fish
    ```

**Optional: Add shell integration so the correct env applies as you `cd`:**
  - Bash:
    ````
    echo 'source ~/.codex-cli-env/shell/codexenv.bash' >> ~/.bashrc
    source ~/.bashrc
    ````
  - Fish:
    ````
    echo 'source ~/.codex-cli-env/shell/codexenv.fish' >> ~/.config/fish/config.fish
    source ~/.config/fish/config.fish
    ````

Note: Paths can be overridden with env vars: `CODEXENV_ROOT` (default `~/.codex-cli-env`), `CODEXENV_CODEX_HOME` (default `~/.codex`). For npm integration you can use `CODEXENV_NPM` to set the npm binary and `CODEXENV_NPM_PACKAGE` to override the package name (default `@openai/codex`).

## Commands

- `codexenv init [name] [--npm-install] [--npm-binary npm] [--npm-package @openai/codex] [--force-npm]`: Initialize management. Migrates an existing `~/.codex` into env `[name]` (default `global`), sets it as global, and makes `~/.codex` a symlink. With `--npm-install`, runs `npm install -g @openai/codex` (configurable via flags/env vars). You can choose any name; if you later change your mind, use `codexenv rename`.
- `codexenv list`: List environments; `*` marks the env active for the current directory.
- `codexenv global [name]`: Show or set the global env.
- `codexenv local [name] [--unset] [--apply]`: Show or set `.codexenv-local` in the current directory; `--apply` immediately updates `~/.codex`.
- `codexenv create <name> [--clone-from <env>] [--npm-install] [--npm-binary npm] [--npm-package @openai/codex] [--force-npm]`: Create a new env directory; optionally clone files from another env. With `--npm-install`, runs `npm install -g @openai/codex`.
- `codexenv delete <name> [--yes]`: Delete an env. If it's the last env, `--yes` restores files to a physical `~/.codex` to ensure Codex CLI still works.
- `codexenv resolve`: Print the effective env name for the current directory.
- `codexenv apply-symlink`: Ensure `~/.codex` symlink matches the effective env. Used by shell integration.
- `codexenv rename <old> <new>`: Rename an environment directory from `<old>` to `<new>`. If `<old>` was the global env, the global is updated, and the `~/.codex` symlink is refreshed if it pointed to `<old>`.

## Behavior

- Environments live under `~/.codex-cli-env/envs/`.
- The active env for a directory is resolved by searching upward for `.codexenv-local`; if none is found, the global env is used.
- Shell integration hooks update the `~/.codex` symlink automatically as you change directories.
- Safety: The tool refuses to replace a non-symlink `~/.codex` unless you run `codexenv init` (which migrates safely).

## Notes

- This tool can install `@openai/codex` globally when you pass `--npm-install`. Otherwise ensure Codex CLI is installed globally via npm.
- Linux (and WSL) are the supported targets currently.

## Testing

Quick start for running tests locally without touching your real `~/.codex`:

1) Create and activate a virtualenv

```
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dev requirements

```
pip install -r requirements_dev.txt
```

3) Run pytest

```
pytest -q
```

Tips:
- Use environment overrides when running the CLI in tests to avoid modifying your real home:
  - `CODEXENV_ROOT=$PWD/.tmp_root CODEXENV_CODEX_HOME=$PWD/.tmp_codex python3 bin/codexenv ...`
- Ensure `bin/` is executable or call the script explicitly with `python3 bin/codexenv`.
