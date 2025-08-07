#!/usr/bin/env bash
# SSM (Sealed Secret Manager) bash completion script
#
# Installation:
# - Copy to ~/.bash_completion.d/_ssm (create directory if needed)
# - Or source directly: source _ssm_completion.bash
# - Or install system-wide: sudo cp _ssm_completion.bash /etc/bash_completion.d/ssm

_ssm_completion() {
    local cur prev opts commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Global options
    local global_opts="--dir --skip-check --controller-namespace -h --help"
    
    # Commands
    local commands="create update list apply decrypt"

    # If we're completing the first argument (command)
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        if [[ ${cur} == -* ]]; then
            COMPREPLY=($(compgen -W "${global_opts}" -- ${cur}))
        else
            COMPREPLY=($(compgen -W "${commands}" -- ${cur}))
        fi
        return 0
    fi

    # Get the command (first non-option argument)
    local command=""
    local i=1
    while [[ $i -lt ${COMP_CWORD} ]]; do
        if [[ ${COMP_WORDS[$i]} != -* ]]; then
            command="${COMP_WORDS[$i]}"
            break
        fi
        ((i++))
    done

    # Handle global options that take arguments
    case "${prev}" in
        --dir)
            COMPREPLY=($(compgen -d -- ${cur}))
            return 0
            ;;
        --controller-namespace|--namespace)
            # Complete with kubernetes namespaces if kubectl is available
            if command -v kubectl >/dev/null 2>&1; then
                local namespaces=$(kubectl get namespaces -o name 2>/dev/null | sed 's|namespace/||' | tr '\n' ' ')
                COMPREPLY=($(compgen -W "${namespaces}" -- ${cur}))
            fi
            return 0
            ;;
    esac

    # Command-specific completions
    case "${command}" in
        create)
            case "${prev}" in
                --namespace)
                    if command -v kubectl >/dev/null 2>&1; then
                        local namespaces=$(kubectl get namespaces -o name 2>/dev/null | sed 's|namespace/||' | tr '\n' ' ')
                        COMPREPLY=($(compgen -W "${namespaces}" -- ${cur}))
                    fi
                    return 0
                    ;;
                *)
                    if [[ ${cur} == -* ]]; then
                        COMPREPLY=($(compgen -W "--namespace -h --help" -- ${cur}))
                    fi
                    return 0
                    ;;
            esac
            ;;
        update|apply)
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "-h --help" -- ${cur}))
            else
                # Complete with YAML files
                COMPREPLY=($(compgen -f -X '!*.y*ml' -- ${cur}))
            fi
            return 0
            ;;
        list)
            case "${prev}" in
                --namespace)
                    if command -v kubectl >/dev/null 2>&1; then
                        local namespaces=$(kubectl get namespaces -o name 2>/dev/null | sed 's|namespace/||' | tr '\n' ' ')
                        COMPREPLY=($(compgen -W "${namespaces}" -- ${cur}))
                    fi
                    return 0
                    ;;
                *)
                    if [[ ${cur} == -* ]]; then
                        COMPREPLY=($(compgen -W "--namespace -h --help" -- ${cur}))
                    fi
                    return 0
                    ;;
            esac
            ;;
        decrypt)
            case "${prev}" in
                --namespace)
                    if command -v kubectl >/dev/null 2>&1; then
                        local namespaces=$(kubectl get namespaces -o name 2>/dev/null | sed 's|namespace/||' | tr '\n' ' ')
                        COMPREPLY=($(compgen -W "${namespaces}" -- ${cur}))
                    fi
                    return 0
                    ;;
                *)
                    if [[ ${cur} == -* ]]; then
                        COMPREPLY=($(compgen -W "--namespace -h --help" -- ${cur}))
                    else
                        # Complete with YAML files and secret names
                        local yaml_files=$(compgen -f -X '!*.y*ml' -- ${cur})
                        local secret_names=""
                        if command -v kubectl >/dev/null 2>&1; then
                            secret_names=$(kubectl get secrets -o name 2>/dev/null | sed 's|secret/||' | tr '\n' ' ')
                        fi
                        COMPREPLY=($(compgen -W "${yaml_files} ${secret_names}" -- ${cur}))
                    fi
                    return 0
                    ;;
            esac
            ;;
        *)
            # Unknown command, offer global options
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "${global_opts}" -- ${cur}))
            fi
            return 0
            ;;
    esac
}

# Register the completion function
complete -F _ssm_completion ssm
