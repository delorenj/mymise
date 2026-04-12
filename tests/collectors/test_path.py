import os

from mymise.collectors.path import PathCollector
from mymise.models import ToolSource


def test_path_collector_name():
    collector = PathCollector()
    assert collector.name == "path"


def test_path_collector_available():
    collector = PathCollector()
    assert collector.available() is True


def test_path_collector_collect_basic(tmp_path, monkeypatch):
    # Setup mock PATH
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    tool1 = bin_dir / "tool1"
    tool1.write_text("binary1")
    tool1.chmod(0o755)

    tool2 = bin_dir / "tool2"
    tool2.write_text("binary2")
    # Not executable, should be skipped
    tool2.chmod(0o644)

    monkeypatch.setenv("PATH", str(bin_dir))

    collector = PathCollector()
    tools = collector.collect()

    assert len(tools) == 1
    assert tools[0].name == "tool1"
    assert ToolSource.PATH in tools[0].sources
    assert tools[0].binary_path == str(tool1.resolve())


def test_path_collector_skips_non_existent(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    # Don't create it

    monkeypatch.setenv("PATH", str(bin_dir))

    collector = PathCollector()
    tools = collector.collect()

    assert len(tools) == 0


def test_path_collector_deduplicates_symlinks(tmp_path, monkeypatch):
    # Setup mock PATH with symlinks
    bin_dir1 = tmp_path / "bin1"
    bin_dir1.mkdir()
    bin_dir2 = tmp_path / "bin2"
    bin_dir2.mkdir()

    actual_bin = bin_dir1 / "real_tool"
    actual_bin.write_text("real")
    actual_bin.chmod(0o755)

    link_in_bin2 = bin_dir2 / "link_tool"
    link_in_bin2.symlink_to(actual_bin)

    # Both directories in PATH
    monkeypatch.setenv("PATH", f"{bin_dir1}{os.pathsep}{bin_dir2}")

    collector = PathCollector()
    tools = collector.collect()

    # Should only have one tool (the real one), even if reached via two names/paths
    # Actually, if they have different names but same target, should they be deduplicated?
    # AC says: "follow symlinks and deduplicate by resolved target"
    # If I have 'real_tool' and 'link_tool' pointing to same file, AC implies I should only get one.
    # Usually we want the names. If 'bat' is a symlink to 'batcat', we might want both or one.
    # But AC specifically says "deduplicate by resolved target".

    assert len(tools) == 1
    # Which name to keep? Usually the first one encountered or the target name.
    # Let's assume the first one encountered or just ensure it's length 1.
    assert tools[0].binary_path == str(actual_bin.resolve())


def test_path_collector_multiple_dirs(tmp_path, monkeypatch):
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    dir2 = tmp_path / "dir2"
    dir2.mkdir()

    t1 = dir1 / "t1"
    t1.write_text("t1")
    t1.chmod(0o755)

    t2 = dir2 / "t2"
    t2.write_text("t2")
    t2.chmod(0o755)

    monkeypatch.setenv("PATH", f"{dir1}{os.pathsep}{dir2}")

    collector = PathCollector()
    tools = {t.name: t for t in collector.collect()}

    assert len(tools) == 2
    assert "t1" in tools
    assert "t2" in tools
