#!/bin/bash
# Gemini CLI driver for Ralph
# Uses Gemini CLI's non-interactive mode with JSON output and session resume.

driver_name() {
    echo "gemini"
}

driver_display_name() {
    echo "Gemini CLI"
}

driver_cli_binary() {
    echo "gemini"
}

driver_min_version() {
    echo "0.30.0"
}

driver_check_available() {
    command -v "$(driver_cli_binary)" &>/dev/null
}

driver_valid_tools() {
    VALID_TOOL_PATTERNS=(
        "Read"
        "Write"
        "Edit"
        "Bash"
        "Glob"
        "Grep"
        "WebFetch"
        "WebSearch"
    )
}

driver_supports_tool_allowlist() {
    return 1
}

driver_permission_denial_help() {
    echo "  - $DRIVER_DISPLAY_NAME uses --yolo mode for auto-approval."
    echo "  - ALLOWED_TOOLS in $RALPHRC_FILE is ignored for this driver."
    echo "  - If Gemini blocks an action, check its policy engine settings."
    echo "  - Review Gemini CLI permissions, then restart the loop."
}

driver_build_command() {
    local prompt_file=$1
    local loop_context=$2
    local session_id=$3

    if [[ ! -f "$prompt_file" ]]; then
        echo "ERROR: Prompt file not found: $prompt_file" >&2
        return 1
    fi

    CLAUDE_CMD_ARGS=("$(driver_cli_binary)" "--yolo")

    # Output format
    if [[ "$CLAUDE_OUTPUT_FORMAT" == "json" ]]; then
        CLAUDE_CMD_ARGS+=("-o" "json")
    fi

    # Session resume
    if [[ "$CLAUDE_USE_CONTINUE" == "true" && -n "$session_id" ]]; then
        CLAUDE_CMD_ARGS+=("-r" "$session_id")
    fi

    # Build prompt content from file + loop context
    local prompt_content
    prompt_content=$(cat "$prompt_file")
    if [[ -n "$loop_context" ]]; then
        prompt_content="$loop_context

$prompt_content"
    fi

    # Non-interactive mode with prompt
    CLAUDE_CMD_ARGS+=("-p" "$prompt_content")

    return 0
}

driver_supports_sessions() {
    return 0
}

driver_supports_live_output() {
    return 0
}

driver_prepare_live_command() {
    # Replace json with stream-json for live output
    LIVE_CMD_ARGS=()
    local arg
    for arg in "${CLAUDE_CMD_ARGS[@]}"; do
        if [[ "$arg" == "json" ]]; then
            LIVE_CMD_ARGS+=("stream-json")
        else
            LIVE_CMD_ARGS+=("$arg")
        fi
    done
}

driver_stream_filter() {
    # Gemini stream-json format: extract text content from assistant messages
    echo 'select(.type == "result" or .type == "content") | .result // .content // empty'
}
