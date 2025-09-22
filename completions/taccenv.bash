# bash completion for taccenv
_taccenv_complete() {
  local cur
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"

  # Only complete the first argument (script name). After that, let scripts handle their own flags or default to file completion.
  if (( COMP_CWORD == 1 )); then
    local choices
    choices="$(taccenv --list 2>/dev/null)"
    COMPREPLY=( $(compgen -W "$choices" -- "$cur") )
  else
    # Fallback to filenames once a script is chosen
    COMPREPLY=( $(compgen -f -- "$cur") )
  fi
  return 0
}
complete -F _taccenv_complete taccenv
