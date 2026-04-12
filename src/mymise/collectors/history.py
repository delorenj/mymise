import os
import re
from datetime import UTC, datetime
from pathlib import Path

from mymise.models import DiscoveredTool, ToolSource


class HistoryCollector:
    """Parses zsh extended history format: `: <timestamp>:<duration>;command_text`"""

    name = "history"

    BUILTINS = {
        "alias",
        "bg",
        "break",
        "builtin",
        "cd",
        "command",
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
        "getopts",
        "hash",
        "help",
        "history",
        "jobs",
        "kill",
        "let",
        "local",
        "logout",
        "popd",
        "printf",
        "pushd",
        "pwd",
        "read",
        "readonly",
        "return",
        "set",
        "shift",
        "shopt",
        "source",
        "suspend",
        "test",
        "times",
        "trap",
        "true",
        "type",
        "typeset",
        "ulimit",
        "umask",
        "unalias",
        "unset",
        "wait",
        "[",
        "]",
        "{",
        "}",
    }

    WRAPPERS = {"sudo", "time", "watch", "which", "nohup", "valgrind", "nice", "xargs", "parallel", "env"}

    def __init__(self, history_path: str = "~/.zsh_history") -> None:
        self.history_path = history_path

    def available(self) -> bool:
        """Return True if the history file exists and is readable."""
        try:
            path = Path(self.history_path).expanduser()
            return path.exists() and os.access(path, os.R_OK)
        except Exception:
            return False

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered from zsh history."""
        if not self.available():
            return []

        aggregated = {}  # name -> {"frequency": int, "last_used": datetime}

        try:
            path = Path(self.history_path).expanduser()
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    # Format: : 1712956800:0;ls -la
                    # We are lenient with the duration part (between colons)
                    match = re.match(r"^: (\d+):[^;]*;(.*)$", line)
                    if not match:
                        continue

                    ts_str, command_text = match.groups()
                    try:
                        ts = int(ts_str)
                        dt = datetime.fromtimestamp(ts, tz=UTC)
                    except (ValueError, OSError):
                        continue

                    tools = self._extract_tools(command_text)
                    for tool_name in tools:
                        if tool_name in self.BUILTINS:
                            continue

                        if tool_name not in aggregated:
                            aggregated[tool_name] = {"frequency": 0, "last_used": dt}

                        aggregated[tool_name]["frequency"] += 1
                        if dt > aggregated[tool_name]["last_used"]:
                            aggregated[tool_name]["last_used"] = dt
        except Exception:
            return []

        return [
            DiscoveredTool(
                name=name,
                sources=[ToolSource.HISTORY],
                frequency=data["frequency"],
                last_used=data["last_used"],
            )
            for name, data in aggregated.items()
        ]

    def _extract_tools(self, command_text: str) -> set[str]:
        """Extract tool names from a command string, including pipelines and subshells."""
        # Replace subshell markers and logic operators with a single separator
        text = command_text.replace("$(", " ; ").replace(")", " ; ").replace("`", " ; ")
        text = text.replace("&&", " ; ").replace("||", " ; ")

        # Split by command separators
        segments = re.split(r"[|;>\n\r]", text)

        found = set()
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            parts = segment.split()

            while parts:
                cmd = parts[0]

                # Skip environment variable assignments (e.g., DEBUG=1 ls)
                if "=" in cmd and not cmd.startswith(("/", "./", "../")):
                    parts.pop(0)
                    continue

                # Skip builtins entirely
                if cmd in self.BUILTINS:
                    break

                # Skip flags
                if cmd.startswith("-"):
                    break

                # Handle absolute or relative paths by taking the basename
                name = os.path.basename(cmd) if cmd.startswith(("/", "./", "../")) else cmd

                if name:
                    found.add(name)

                # If it's a wrapper (sudo, which, etc.), continue to the next part
                if cmd in self.WRAPPERS:
                    parts.pop(0)
                    continue

                # Otherwise, we've found the main command for this segment
                break

        return found
