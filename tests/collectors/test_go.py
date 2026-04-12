from unittest.mock import MagicMock, patch

from mymise.collectors.go import GoCollector
from mymise.models import ToolSource


def test_go_collector_name():
    collector = GoCollector()
    assert collector.name == "go"


def test_go_collector_available_true():
    with patch("shutil.which", return_value="/usr/bin/go"):
        collector = GoCollector()
        assert collector.available() is True


def test_go_collector_available_false():
    with patch("shutil.which", return_value=None):
        collector = GoCollector()
        assert collector.available() is False


def test_go_collector_collect_success(tmp_path):
    # Setup mock GOPATH/bin
    go_path = tmp_path / "go"
    bin_dir = go_path / "bin"
    bin_dir.mkdir(parents=True)
    
    (bin_dir / "tool1").write_text("binary1")
    (bin_dir / "tool1").chmod(0o755)
    (bin_dir / "tool2").write_text("binary2")
    (bin_dir / "tool2").chmod(0o755)
    
    with patch("shutil.which", return_value="/usr/bin/go"), \
         patch("subprocess.run") as mock_run:
        
        # Mock go env GOPATH
        mock_run.return_value = MagicMock(stdout=str(go_path), stderr="", returncode=0)
        
        collector = GoCollector()
        tools = collector.collect()
        
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "tool1" in names
        assert "tool2" in names
        assert all(t.sources == [ToolSource.GO] for t in tools)


def test_go_collector_collect_no_bin_dir(tmp_path):
    go_path = tmp_path / "go"
    # bin dir not created
    
    with patch("shutil.which", return_value="/usr/bin/go"), \
         patch("subprocess.run") as mock_run:
        
        mock_run.return_value = MagicMock(stdout=str(go_path), stderr="", returncode=0)
        
        collector = GoCollector()
        tools = collector.collect()
        assert tools == []


def test_go_collector_collect_not_available():
    with patch("shutil.which", return_value=None):
        collector = GoCollector()
        tools = collector.collect()
        assert tools == []
