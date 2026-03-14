import shutil
import subprocess
from pathlib import Path

SHELL_BUILTINS = frozenset(
    {
        "alias",
        "bg",
        "bind",
        "break",
        "builtin",
        "caller",
        "case",
        "cd",
        "command",
        "compgen",
        "complete",
        "continue",
        "declare",
        "dirs",
        "disown",
        "echo",
        "enable",
        "eval",
        "exec",
        "exit",
        "export",
        "false",
        "fc",
        "fg",
        "for",
        "function",
        "getopts",
        "hash",
        "help",
        "history",
        "if",
        "jobs",
        "kill",
        "let",
        "local",
        "logout",
        "mapfile",
        "popd",
        "printf",
        "pushd",
        "pwd",
        "read",
        "readarray",
        "readonly",
        "return",
        "select",
        "set",
        "shift",
        "shopt",
        "source",
        "suspend",
        "test",
        "then",
        "time",
        "times",
        "trap",
        "true",
        "type",
        "typeset",
        "ulimit",
        "umask",
        "unalias",
        "unset",
        "until",
        "wait",
        "while",
    }
)

DEFAULT_HISTORY_PATH = Path.home() / ".zsh_history"


def run_command(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def is_builtin(name: str) -> bool:
    return name.lower() in SHELL_BUILTINS


def normalize_tool_name(name: str) -> str:
    return name.strip().lower()
