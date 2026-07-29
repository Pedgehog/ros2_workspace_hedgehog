# Git Abkürzungen
alias gs='clear && git status'
alias gp='clear && git push'
alias gll='clear && git log --oneline --graph --all'
alias gl='clear && git log --oneline'
alias ga='clear && git add .'
alias gaa='clear && git add . && git status'
alias gc='clear && git commit -m'
alias gac='clear && git add . && git commit -m'
alias gd='clear && git diff'
alias gb='clear && git branch'
alias grw='clear && git rebase -i'
alias gg='clear && git log -4 --oneline && git status'
# Git-Github Issues
alias gch='bash ~/.development/check_issues.sh'
alias gi='bash ~/.development/print_issues.sh'

alias mach='sudo'
alias vs='code . && exit'
alias cls='clear'

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

alias get_idf='. $HOME/esp/esp-idf/export.sh'
alias testing='uv run pytest'
alias treee='tree -I "venv|.git|__pycache__|node_modules"'
alias vs='code . && exit'


alias rosb='source helperscrips/manual_console_temp.sh'
