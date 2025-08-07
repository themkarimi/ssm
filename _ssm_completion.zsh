#compdef ssm
# SSM (Sealed Secret Manager) completion script
# Installation:
# - Copy to ~/.zsh/completions/_ssm
# - Add 'fpath=(~/.zsh/completions $fpath)' to ~/.zshrc
# - Run 'autoload -U compinit && compinit'

_ssm() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    # Define global options
    local -a global_opts
    global_opts=(
        '--dir[Directory for secrets]:directory:_files -/'
        '--skip-check[Skip tool checks]'
        '--controller-namespace[Sealed secrets controller namespace]:namespace:'
        '(-h --help)'{-h,--help}'[Show help]'
    )

    # Define commands
    local -a commands
    commands=(
        'create:Create a new SealedSecret'
        'update:Update an existing SealedSecret'
        'list:List all SealedSecrets'
        'apply:Apply SealedSecret to cluster'
        'decrypt:Decrypt and view a SealedSecret'
    )

    _arguments -C \
        $global_opts \
        '1: :->command' \
        '*:: :->args' && return 0

    case $state in
        command)
            _describe -t commands 'ssm commands' commands && return 0
            ;;
        args)
            case $line[1] in
                create)
                    _arguments \
                        ':name:' \
                        '--namespace[Target namespace]:namespace:_ssm_namespaces' \
                        '(-h --help)'{-h,--help}'[Show help]' && return 0
                    ;;
                update)
                    _arguments \
                        ':file:_files -g "*.y(a|)ml"' \
                        '(-h --help)'{-h,--help}'[Show help]' && return 0
                    ;;
                list)
                    _arguments \
                        '--namespace[Filter by namespace]:namespace:_ssm_namespaces' \
                        '(-h --help)'{-h,--help}'[Show help]' && return 0
                    ;;
                apply)
                    _arguments \
                        ':file:_files -g "*.y(a|)ml"' \
                        '(-h --help)'{-h,--help}'[Show help]' && return 0
                    ;;
                decrypt)
                    _arguments \
                        ':target:_ssm_decrypt_targets' \
                        '--namespace[Namespace for secret name]:namespace:_ssm_namespaces' \
                        '(-h --help)'{-h,--help}'[Show help]' && return 0
                    ;;
            esac
            ;;
    esac
}

# Helper function to complete namespaces
_ssm_namespaces() {
    local -a namespaces
    if command -v kubectl >/dev/null 2>&1; then
        namespaces=(${(f)"$(kubectl get namespaces -o name 2>/dev/null | sed 's|namespace/||')"})
        _describe 'namespaces' namespaces
    else
        _message "kubectl not available"
    fi
}

# Helper function for decrypt targets (files or secret names)
_ssm_decrypt_targets() {
    local -a targets
    
    # Add YAML files
    _files -g "*.y(a|)ml" && return 0
    
    # If kubectl is available, also suggest secret names
    if command -v kubectl >/dev/null 2>&1; then
        targets=(${(f)"$(kubectl get secrets -o name 2>/dev/null | sed 's|secret/||')"})
        if [[ ${#targets[@]} -gt 0 ]]; then
            _describe 'secret names' targets
        fi
    fi
}

# Only define the completion function, don't execute it

# vim: ft=zsh

# vim: ft=zsh
