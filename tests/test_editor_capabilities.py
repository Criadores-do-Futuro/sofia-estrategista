import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.editor_capabilities import CapabilityEvidence, EditorEvidence, select_editor


def ready(*names):
    return EditorEvidence(
        availability="available",
        source="verificação local da conexão",
        capabilities={name: CapabilityEvidence("verified", "teste de capacidade") for name in names},
    )


class SelectionTests(unittest.TestCase):
    def test_explicit_choice_never_silently_changes_editor(self):
        result = select_editor("capcut", ["mask"], {"capcut": ready("cut"), "davinci": ready("mask")})
        self.assertEqual((result.status, result.editor), ("blocked", None))
        self.assertIn("Capacidade não verificada: mask", result.blockers["capcut"])
        self.assertNotIn("davinci", result.blockers)

    def test_auto_selects_only_editor_with_every_required_capability(self):
        result = select_editor("auto", ["cut", "caption"], {"capcut": ready("cut"), "davinci": ready("cut", "caption")})
        self.assertEqual((result.status, result.editor), ("ready", "davinci"))
        self.assertIn("Capacidade não verificada: caption", result.blockers["capcut"])

    def test_unavailable_and_unsupported_are_explained_separately(self):
        evidence = EditorEvidence("unavailable", {"cut": CapabilityEvidence("unsupported")})
        result = select_editor("davinci", ["cut"], {"davinci": evidence})
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.blockers["davinci"], ("Editor indisponível neste ambiente", "Capacidade não suportada: cut"))

    def test_absent_evidence_is_not_treated_as_working(self):
        result = select_editor("auto", ["cut"], {})
        self.assertEqual(result.status, "blocked")
        self.assertEqual(set(result.blockers), {"capcut", "davinci"})
        self.assertIn("Disponibilidade do editor não verificada", result.blockers["capcut"])

    def test_preference_breaks_tie_only_between_capable_editors(self):
        facts = {"capcut": ready("cut"), "davinci": ready("cut")}
        self.assertEqual(select_editor("auto", ["cut"], facts, ("davinci", "capcut")).editor, "davinci")

    def test_verified_facts_need_provenance_and_inputs_are_validated(self):
        with self.assertRaises(ValueError):
            CapabilityEvidence("verified")
        with self.assertRaises(ValueError):
            EditorEvidence("available")
        with self.assertRaises(ValueError):
            select_editor("auto", [], {})
        with self.assertRaises(ValueError):
            select_editor("auto", ["cut"], {}, ("capcut", "capcut"))


if __name__ == "__main__":
    unittest.main()
