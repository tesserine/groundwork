import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CONTRACT_DOC = ROOT / "docs" / "architecture" / "forge-deployment-identity.md"


class ForgeDeploymentIdentityDocsTests(unittest.TestCase):
    def test_readme_links_to_groundwork_deployment_identity_contract(self) -> None:
        readme = README.read_text(encoding="utf-8")

        self.assertIn("GROUNDWORK_* deployment identity", readme)
        self.assertIn("docs/architecture/forge-deployment-identity.md", readme)

    def test_deployment_identity_contract_documents_all_atoms(self) -> None:
        body = CONTRACT_DOC.read_text(encoding="utf-8")

        for variable in [
            "GROUNDWORK_FORGE_TYPE",
            "GROUNDWORK_FORGE_ENDPOINT",
            "GROUNDWORK_FORGE_OWNER",
            "GROUNDWORK_FORGE_NAME",
            "GROUNDWORK_FORGE_TRACKER_ID",
            "GROUNDWORK_FORGE_REPO_ID",
        ]:
            with self.subTest(variable=variable):
                self.assertIn(variable, body)

        self.assertIn("Forge-assigned?", body)
        self.assertIn("non-derivable", body)
        self.assertIn("github", body)
        self.assertIn("weforge.build", body)
        self.assertIn("operator", body)
        self.assertIn("weforge", body)
        self.assertIn("4", body)
        self.assertIn("<repo Int>", body)

    def test_deployment_identity_contract_assigns_composition_to_issue_363(self) -> None:
        body = CONTRACT_DOC.read_text(encoding="utf-8")

        self.assertIn("#363", body)
        self.assertIn("todo_query_url = https://todo.${GROUNDWORK_FORGE_ENDPOINT}/query", body)
        self.assertIn("git_query_url = https://git.${GROUNDWORK_FORGE_ENDPOINT}/query", body)
        self.assertIn(
            "ssh_remote = git@git.${GROUNDWORK_FORGE_ENDPOINT}:~${GROUNDWORK_FORGE_OWNER}/${GROUNDWORK_FORGE_NAME}",
            body,
        )


if __name__ == "__main__":
    unittest.main()
