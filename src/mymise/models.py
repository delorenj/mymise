from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ToolCategory(StrEnum):
    RUNTIME = "runtime"
    PACKAGE_MANAGER = "pkg-mgr"
    CLI_TOOL = "cli-tool"
    LANGUAGE_TOOL = "lang-tool"
    SYSTEM_UTILITY = "sys-util"


class ToolSource(StrEnum):
    HISTORY = "history"
    PATH = "path"
    APT = "apt"
    CARGO = "cargo"
    NPM = "npm"
    PIPX = "pipx"
    MISE = "mise"
    SNAP = "snap"
    GO = "go"
    UV = "uv"


class BackendType(StrEnum):
    AQUA = "aqua"
    GITHUB = "github"
    ASDF = "asdf"
    CORE = "core"
    PIPX = "pipx"
    CARGO = "cargo"
    NPM = "npm"
    GO = "go"


class DiscoveredTool(BaseModel):
    name: str
    sources: list[ToolSource]
    frequency: int = 0
    last_used: datetime | None = None
    binary_path: str | None = None
    installed_by: list[ToolSource] = []
    category: ToolCategory | None = None


class DiscoveryResult(BaseModel):
    schema_version: str = "1.0.0"
    scan_timestamp: datetime
    hostname: str
    user: str
    scan_duration_seconds: float
    tools: list[DiscoveredTool]


class ResolvedTool(BaseModel):
    name: str
    backend: BackendType
    registry_entry: str
    install_command: str
    original: DiscoveredTool


class UnresolvedTool(BaseModel):
    name: str
    original: DiscoveredTool
    suggested_actions: list[str] = []


class ResolutionResult(BaseModel):
    schema_version: str = "1.0.0"
    resolution_timestamp: datetime
    resolved: list[ResolvedTool]
    unresolved: list[UnresolvedTool]
    resolution_rate: float
