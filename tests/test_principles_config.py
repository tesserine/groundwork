import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from tooling.principles_config import (
    EMBEDDED_CORPUS_PATH,
    PRINCIPLES_CONFIG_SCHEMA,
    PrinciplesConfigError,
    PrinciplesCorpusConfig,
    _schema_errors,
    default_config_path,
    load_principles_config,
    parse_principles_config,
    render_principles_config,
    resolved_corpus_path,
    write_principles_config,
)


ROOT = Path(__file__).resolve().parents[1]


class ZeroConfigDefaultTests(unittest.TestCase):
    """The zero-config path is first-class: every absent-configuration shape
    selects the embedded default."""

    def test_missing_config_file_selects_embedded_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = load_principles_config(Path(directory) / "principles.toml")

        self.assertEqual(config, PrinciplesCorpusConfig.embedded())

    def test_empty_document_selects_embedded_default(self) -> None:
        config = parse_principles_config({})

        self.assertEqual(config, PrinciplesCorpusConfig.embedded())

    def test_empty_config_file_selects_embedded_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "principles.toml"
            config_file.write_text("", encoding="utf-8")

            config = load_principles_config(config_file)

        self.assertEqual(config, PrinciplesCorpusConfig.embedded())

    def test_explicit_embedded_source_selects_embedded_default(self) -> None:
        config = parse_principles_config({"corpus": {"source": "embedded"}})

        self.assertEqual(config, PrinciplesCorpusConfig.embedded())


class ConfiguredSourceTests(unittest.TestCase):
    def test_local_path_source_parses_to_absolute_path(self) -> None:
        config = parse_principles_config({"corpus": {"source": "path", "path": "/srv/corpus"}})

        self.assertEqual(config.source, "path")
        self.assertEqual(config.path, Path("/srv/corpus"))

    def test_git_source_parses_url_and_optional_ref(self) -> None:
        config = parse_principles_config(
            {"corpus": {"source": "git", "url": "https://example.org/owner/corpus", "ref": "v1.0.0"}}
        )

        self.assertEqual(config.source, "git")
        self.assertEqual(config.url, "https://example.org/owner/corpus")
        self.assertEqual(config.ref, "v1.0.0")

    def test_git_source_ref_defaults_to_none(self) -> None:
        config = parse_principles_config(
            {"corpus": {"source": "git", "url": "https://example.org/owner/corpus"}}
        )

        self.assertIsNone(config.ref)

    def test_sample_external_corpus_config_file_validates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "principles.toml"
            config_file.write_text(
                '[corpus]\nsource = "git"\nurl = "https://example.org/owner/corpus"\n',
                encoding="utf-8",
            )

            config = load_principles_config(config_file)

        self.assertEqual(config.source, "git")


class InvalidConfigTests(unittest.TestCase):
    """A present configuration never silently degrades to the default."""

    def test_unknown_source_is_rejected(self) -> None:
        with self.assertRaises(PrinciplesConfigError):
            parse_principles_config({"corpus": {"source": "carrier-pigeon"}})

    def test_git_source_without_url_is_rejected(self) -> None:
        with self.assertRaises(PrinciplesConfigError):
            parse_principles_config({"corpus": {"source": "git"}})

    def test_path_source_without_path_is_rejected(self) -> None:
        with self.assertRaises(PrinciplesConfigError):
            parse_principles_config({"corpus": {"source": "path"}})

    def test_relative_corpus_path_is_rejected_with_named_error(self) -> None:
        with self.assertRaises(PrinciplesConfigError) as caught:
            parse_principles_config({"corpus": {"source": "path", "path": "relative/corpus"}})

        self.assertIn("corpus/path", caught.exception.paths)

    def test_unknown_top_level_key_is_rejected(self) -> None:
        with self.assertRaises(PrinciplesConfigError):
            parse_principles_config({"corpse": {"source": "embedded"}})

    def test_extraneous_key_on_embedded_source_is_rejected(self) -> None:
        with self.assertRaises(PrinciplesConfigError):
            parse_principles_config(
                {"corpus": {"source": "embedded", "url": "https://example.org/owner/corpus"}}
            )

    def test_invalid_toml_is_rejected_with_named_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "principles.toml"
            config_file.write_text("[corpus\n", encoding="utf-8")

            with self.assertRaises(PrinciplesConfigError) as caught:
                load_principles_config(config_file)

        self.assertIn("<toml>", caught.exception.paths)


class NamedConceptTests(unittest.TestCase):
    """The configured source and the resolved local corpus are distinct,
    named concepts."""

    def test_default_config_path_honors_xdg_config_home(self) -> None:
        path = default_config_path({"XDG_CONFIG_HOME": "/etc/xdg-test"})

        self.assertEqual(path, Path("/etc/xdg-test/groundwork/principles.toml"))

    def test_default_config_path_falls_back_to_home_dot_config(self) -> None:
        path = default_config_path({"HOME": "/home/someone"})

        self.assertEqual(path, Path("/home/someone/.config/groundwork/principles.toml"))

    def test_default_config_path_without_home_raises_named_error(self) -> None:
        with self.assertRaises(PrinciplesConfigError):
            default_config_path({})

    def test_resolved_corpus_path_is_stable_under_runtime_root(self) -> None:
        self.assertEqual(
            resolved_corpus_path("/home/someone/.groundwork"),
            Path("/home/someone/.groundwork/principles"),
        )

    def test_embedded_corpus_path_is_in_tree(self) -> None:
        self.assertEqual(EMBEDDED_CORPUS_PATH, ROOT / "principles")


class RenderConfigTests(unittest.TestCase):
    """Rendering produces canonical TOML the parser reads back to an equal
    config — the recording surface the self-installer writes operator corpus
    inputs through."""

    CONFIGS = [
        PrinciplesCorpusConfig.embedded(),
        PrinciplesCorpusConfig(source="path", path=Path("/srv/corpus")),
        PrinciplesCorpusConfig(source="git", url="https://example.org/owner/corpus"),
        PrinciplesCorpusConfig(source="git", url="https://example.org/owner/corpus", ref="v1.0.0"),
    ]

    def test_render_round_trips_every_source_kind(self) -> None:
        for config in self.CONFIGS:
            with self.subTest(config=config):
                rendered = render_principles_config(config)

                self.assertEqual(parse_principles_config(tomllib.loads(rendered)), config)

    def test_render_escapes_quotes_and_backslashes_in_operator_values(self) -> None:
        config = PrinciplesCorpusConfig(
            source="git",
            url='https://example.org/o"dd\\corpus',
            ref='re"f\\1',
        )

        rendered = render_principles_config(config)

        self.assertEqual(parse_principles_config(tomllib.loads(rendered)), config)

    def test_write_creates_parent_directories_and_loads_back_equal(self) -> None:
        config = PrinciplesCorpusConfig(source="git", url="https://example.org/owner/corpus")
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "groundwork" / "principles.toml"

            write_principles_config(config, config_file)

            self.assertEqual(load_principles_config(config_file), config)


class SchemaAgreementTests(unittest.TestCase):
    """The stdlib structural validator (the operational home, usable in
    deployments without third-party packages) and the JSON Schema (the
    documentation and conformance contract) must judge the same documents
    the same way. Absolute-path enforcement is a semantic check layered on
    top of structure and is deliberately outside this matrix."""

    DOCUMENTS = [
        {},
        {"corpus": {"source": "embedded"}},
        {"corpus": {"source": "path", "path": "/srv/corpus"}},
        {"corpus": {"source": "git", "url": "https://example.org/owner/corpus"}},
        {"corpus": {"source": "git", "url": "https://example.org/owner/corpus", "ref": "v1"}},
        {"corpus": {"source": "carrier-pigeon"}},
        {"corpus": {"source": "git"}},
        {"corpus": {"source": "path"}},
        {"corpus": {"source": "path", "path": ""}},
        {"corpus": {"source": "git", "url": ""}},
        {"corpus": {"source": "git", "url": "https://example.org/x", "ref": ""}},
        {"corpus": {"source": "embedded", "url": "https://example.org/x"}},
        {"corpus": {"source": "path", "path": "/srv/corpus", "url": "https://example.org/x"}},
        {"corpus": "not-a-table"},
        {"corpus": {}},
        {"corpse": {"source": "embedded"}},
        {"corpus": {"source": "embedded"}, "extra": 1},
    ]

    def test_code_validator_agrees_with_the_schema_contract(self) -> None:
        from jsonschema import Draft202012Validator

        validator = Draft202012Validator(json.loads(PRINCIPLES_CONFIG_SCHEMA.read_text(encoding="utf-8")))

        for document in self.DOCUMENTS:
            with self.subTest(document=document):
                self.assertEqual(
                    validator.is_valid(document),
                    not _schema_errors(document),
                )


if __name__ == "__main__":
    unittest.main()
