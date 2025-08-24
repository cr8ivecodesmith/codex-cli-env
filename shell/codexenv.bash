# Codexenv Bash integration
# Source this file from your ~/.bashrc:
#   source /path/to/repo/shell/codexenv.bash

if command -v codexenv >/dev/null 2>&1; then
  __codexenv_auto() {
    codexenv apply-symlink --quiet >/dev/null 2>&1 || true
  }

  case ":${PROMPT_COMMAND:-}:" in
    *:"__codexenv_auto":*) ;;
    *) PROMPT_COMMAND="__codexenv_auto${PROMPT_COMMAND:+; $PROMPT_COMMAND}" ;;
  esac
fi

