# Codexenv Fish integration
# Source this file from your ~/.config/fish/config.fish or use fisher:
#   source /path/to/repo/shell/codexenv.fish

function __codexenv_auto --on-variable PWD --description 'Auto-apply Codex env symlink'
    if type -q codexenv
        codexenv apply-symlink --quiet >/dev/null 2>&1
    end
end

