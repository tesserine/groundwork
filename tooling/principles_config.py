"""Principles-corpus configuration: the deployment-owned selection surface.

Two distinct concepts live here, and the distinction is load-bearing:

- The **configured source** — where the corpus comes from (`embedded`,
  `path`, or `git`), declared in a deployment-owned config file outside the
  methodology tree. Absent file, empty document, or absent ``[corpus]``
  table all select the embedded default: zero-config is the first-class
  ordinary path, not an error path.
- The **resolved local corpus** — the stable local location the resolution
  layer materializes the configured source into, and the only location
  reckon reads during reasoning. Resolution never live-fetches a remote
  mid-reckon.

This module owns parsing and validation of the configured source. The
materialization step that produces the resolved local corpus belongs to the
resolution layer (setup time), not here.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PRINCIPLES_CONFIG_SCHEMA = ROOT / "schemas" / "principles-config.schema.json"

# The embedded default corpus shipped in the groundwork tree.
EMBEDDED_CORPUS_PATH = ROOT / "principles"

# Resolved-local-corpus directory name under the managed runtime root
# (`~/.groundwork`). The resolution layer materializes the configured source
# here; reckon's documented consultation target is this location.
RESOLVED_CORPUS_DIRECTORY_NAME = "principles"

CONFIG_FILE_RELATIVE_PATH = Path("groundwork") / "principles.toml"

SOURCE_EMBEDDED = "embedded"
SOURCE_PATH = "path"
SOURCE_GIT = "git"


class PrinciplesConfigError(ValueError):
    def __init__(self, errors: list[tuple[str, str]]) -> None:
        self.errors = errors
        self.paths = [path for path, _message in errors]
        super().__init__(self._format())

    def _format(self) -> str:
        return "; ".join(f"{path}: {message}" for path, message in self.errors)


@dataclass(frozen=True)
class PrinciplesCorpusConfig:
    """The configured corpus source, after parsing and validation."""

    source: str
    path: Path | None = None
    url: str | None = None
    ref: str | None = None

    @classmethod
    def embedded(cls) -> "PrinciplesCorpusConfig":
        return cls(source=SOURCE_EMBEDDED)


def default_config_path(environment: Mapping[str, str] | None = None) -> Path:
    """Deployment config location: ``$XDG_CONFIG_HOME/groundwork/principles.toml``,
    falling back to ``~/.config/groundwork/principles.toml``."""
    env = os.environ if environment is None else environment
    xdg_config_home = env.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / CONFIG_FILE_RELATIVE_PATH
    home = env.get("HOME")
    if not home:
        raise PrinciplesConfigError(
            [("<environment>", "cannot locate the principles config: neither XDG_CONFIG_HOME nor HOME is set")]
        )
    return Path(home) / ".config" / CONFIG_FILE_RELATIVE_PATH


def resolved_corpus_path(runtime_root: Path | str) -> Path:
    """The stable resolved-local-corpus location under a runtime root."""
    return Path(runtime_root) / RESOLVED_CORPUS_DIRECTORY_NAME


def load_principles_config(
    path: Path | str | None = None,
    environment: Mapping[str, str] | None = None,
) -> PrinciplesCorpusConfig:
    """Load the configured corpus source.

    A missing config file selects the embedded default. A present but
    unreadable, unparsable, or schema-invalid file raises
    :class:`PrinciplesConfigError` with named errors — a present
    configuration never silently degrades to the default.
    """
    config_path = Path(path) if path is not None else default_config_path(environment)
    if not config_path.exists():
        return PrinciplesCorpusConfig.embedded()

    try:
        raw = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise PrinciplesConfigError([("<read>", f"cannot read principles config {config_path}: {error}")]) from error

    try:
        document = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as error:
        raise PrinciplesConfigError(
            [("<toml>", f"{config_path.name} is invalid TOML: {error}")]
        ) from error

    return parse_principles_config(document)


def render_principles_config(config: PrinciplesCorpusConfig) -> str:
    """Render a configured source as canonical TOML.

    The recording surface for operator corpus inputs: the self-installer
    writes what the operator supplied through here, and what this renders
    always parses back to an equal config (round-trip invariant held by
    tests/test_principles_config.py).
    """
    lines = ["[corpus]", f"source = {_toml_string(config.source)}"]
    if config.path is not None:
        lines.append(f"path = {_toml_string(str(config.path))}")
    if config.url is not None:
        lines.append(f"url = {_toml_string(config.url)}")
    if config.ref is not None:
        lines.append(f"ref = {_toml_string(config.ref)}")
    return "\n".join(lines) + "\n"


def write_principles_config(config: PrinciplesCorpusConfig, path: Path | str) -> None:
    """Atomically record a configured source at ``path``, creating parents."""
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = config_path.with_name(config_path.name + ".tmp")
    temporary.write_text(render_principles_config(config), encoding="utf-8")
    temporary.replace(config_path)


def _toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = "".join(f"\\u{ord(ch):04x}" if ord(ch) < 0x20 or ch == "\x7f" else ch for ch in escaped)
    return f'"{escaped}"'


def parse_principles_config(document: dict[str, Any]) -> PrinciplesCorpusConfig:
    errors = _schema_errors(document)
    if errors:
        raise PrinciplesConfigError(errors)

    corpus = document.get("corpus")
    if corpus is None:
        return PrinciplesCorpusConfig.embedded()

    source = corpus["source"]
    if source == SOURCE_EMBEDDED:
        return PrinciplesCorpusConfig.embedded()
    if source == SOURCE_PATH:
        corpus_path = Path(corpus["path"])
        if not corpus_path.is_absolute():
            raise PrinciplesConfigError(
                [("corpus/path", f"corpus path must be absolute: {corpus_path}")]
            )
        return PrinciplesCorpusConfig(source=SOURCE_PATH, path=corpus_path)
    return PrinciplesCorpusConfig(source=SOURCE_GIT, url=corpus["url"], ref=corpus.get("ref"))


_CORPUS_KEYS_BY_SOURCE: dict[str, dict[str, set[str]]] = {
    SOURCE_EMBEDDED: {"required": set(), "allowed": {"source"}},
    SOURCE_PATH: {"required": {"path"}, "allowed": {"source", "path"}},
    SOURCE_GIT: {"required": {"url"}, "allowed": {"source", "url", "ref"}},
}


def _schema_errors(document: dict[str, Any]) -> list[tuple[str, str]]:
    """Structural validation of the config document.

    Deliberately stdlib-only: setup-time resolution runs in deployments
    that carry no third-party packages (the same constraint
    the installer observes). The JSON Schema at
    ``schemas/principles-config.schema.json`` remains the documentation
    and conformance contract for the same shape; CI holds the two in
    agreement (tests/test_principles_config.py).
    """
    errors: list[tuple[str, str]] = []

    for key in document:
        if key != "corpus":
            errors.append((key, f"unknown key `{key}`; the config holds only a `corpus` table"))
    if errors:
        return errors

    if "corpus" not in document:
        return errors

    corpus = document["corpus"]
    if not isinstance(corpus, dict):
        return [("corpus", "corpus must be a table")]

    source = corpus.get("source")
    if not isinstance(source, str) or source not in _CORPUS_KEYS_BY_SOURCE:
        return [
            (
                "corpus/source",
                "corpus must declare source as one of `embedded` | `path` | `git`",
            )
        ]

    keys = _CORPUS_KEYS_BY_SOURCE[source]
    for key in sorted(keys["required"] - corpus.keys()):
        errors.append((f"corpus/{key}", f"corpus source `{source}` requires `{key}`"))
    for key in sorted(corpus.keys() - keys["allowed"]):
        errors.append((f"corpus/{key}", f"`{key}` is not a valid key for corpus source `{source}`"))
    for key in sorted(keys["allowed"] - {"source"}):
        value = corpus.get(key)
        if value is not None and (not isinstance(value, str) or not value):
            errors.append((f"corpus/{key}", f"`{key}` must be a non-empty string"))

    return errors
