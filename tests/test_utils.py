from mymise.utils import is_builtin, normalize_tool_name


def test_is_builtin_recognizes_builtins() -> None:
    assert is_builtin("cd")
    assert is_builtin("export")
    assert is_builtin("echo")


def test_is_builtin_rejects_tools() -> None:
    assert not is_builtin("bat")
    assert not is_builtin("ripgrep")
    assert not is_builtin("jq")


def test_normalize_tool_name() -> None:
    assert normalize_tool_name("  Bat  ") == "bat"
    assert normalize_tool_name("JQ") == "jq"
