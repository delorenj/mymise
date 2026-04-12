import pytest
from pathlib import Path
from datetime import datetime, timezone
from mymise.collectors.history import HistoryCollector
from mymise.models import ToolSource

def test_history_collector_name():
    collector = HistoryCollector()
    assert collector.name == "history"

def test_history_collector_available_true(tmp_path):
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(": 1712956800:0;ls\n")
    collector = HistoryCollector(history_path=str(history_file))
    assert collector.available() is True

def test_history_collector_available_false(tmp_path):
    history_file = tmp_path / ".non_existent_history"
    collector = HistoryCollector(history_path=str(history_file))
    assert collector.available() is False

def test_history_collector_collect_simple(tmp_path):
    history_file = tmp_path / ".zsh_history"
    # : 1712956800:0;ls -la
    # 1712956800 is 2024-04-12 21:20:00 UTC (approx)
    history_file.write_text(": 1712956800:0;ls -la\n")
    collector = HistoryCollector(history_path=str(history_file))
    tools = collector.collect()
    
    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "ls"
    assert ToolSource.HISTORY in tool.sources
    assert tool.frequency == 1
    assert tool.last_used == datetime.fromtimestamp(1712956800, tz=timezone.utc)

def test_history_collector_collect_multiple_frequency(tmp_path):
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        ": 1000000000:0;ls\n"
        ": 1000000001:0;ls\n"
        ": 1000000002:0;grep foo\n"
    )
    collector = HistoryCollector(history_path=str(history_file))
    tools = {t.name: t for t in collector.collect()}
    
    assert len(tools) == 2
    assert tools["ls"].frequency == 2
    assert tools["ls"].last_used == datetime.fromtimestamp(1000000001, tz=timezone.utc)
    assert tools["grep"].frequency == 1
    assert tools["grep"].last_used == datetime.fromtimestamp(1000000002, tz=timezone.utc)

def test_history_collector_exclude_builtins(tmp_path):
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        ": 1000000000:0;cd /tmp\n"
        ": 1000000001:0;echo hello\n"
        ": 1000000002:0;ls\n"
    )
    collector = HistoryCollector(history_path=str(history_file))
    tools = collector.collect()
    
    assert len(tools) == 1
    assert tools[0].name == "ls"

def test_history_collector_pipelines(tmp_path):
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(": 1000000000:0;cat foo.txt | grep bar | sort\n")
    collector = HistoryCollector(history_path=str(history_file))
    tools = {t.name: t for t in collector.collect()}
    
    assert "cat" in tools
    assert "grep" in tools
    assert "sort" in tools
    assert len(tools) == 3

def test_history_collector_subshells_and_logic(tmp_path):
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        ": 1000000000:0;ls && make || echo failed\n"
        ": 1000000001:0;$(which bat) --version\n"
    )
    collector = HistoryCollector(history_path=str(history_file))
    tools = {t.name: t for t in collector.collect()}
    
    assert "ls" in tools
    assert "make" in tools
    assert "which" in tools
    assert "bat" in tools
    assert "echo" not in tools
    
def test_history_collector_unreadable_file(tmp_path):
    history_file = tmp_path / ".unreadable_history"
    history_file.write_text("some content")
    history_file.chmod(0o000)
    
    collector = HistoryCollector(history_path=str(history_file))
    assert collector.available() is False
    assert collector.collect() == []
    
    # Clean up for other tests
    history_file.chmod(0o666)

def test_history_collector_handles_malformed_lines(tmp_path):
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        "malformed line without colon\n"
        ": 1000000000:ls\n" # missing second colon/duration?
        ": invalid:0;ls\n"
        ": 1000000001:0;ls\n"
    )
    collector = HistoryCollector(history_path=str(history_file))
    tools = collector.collect()
    
    assert len(tools) == 1
    assert tools[0].name == "ls"
    assert tools[0].frequency == 1
