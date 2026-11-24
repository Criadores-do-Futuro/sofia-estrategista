import copy
import importlib.util
import unittest
from pathlib import Path

module_path = Path(__file__).resolve().parents[1] / "plugin" / "scripts" / "validar_plano_editorial.py"
spec = importlib.util.spec_from_file_location("validar_plano_editorial", module_path)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def plan():
    return {
        "version": "1.0",
        "project": {"title": "Exemplo", "editor": "capcut", "creative_format": "dinamismo"},
        "assets": [{"id": "take", "kind": "video", "duration_ms": 3000}],
        "protected_speech": [{"id": "palavra", "asset_id": "take", "source": {"start_ms": 1000, "end_ms": 1400}, "text": "não"}],
        "clips": [
            {"id": "imagem", "asset_id": "take", "track": "v1", "kind": "video", "source": {"start_ms": 500, "end_ms": 2000}, "timeline": {"start_ms": 0, "end_ms": 1500}, "speaker_visible": True},
            {"id": "voz", "asset_id": "take", "track": "a1", "kind": "audio", "source": {"start_ms": 500, "end_ms": 2000}, "timeline": {"start_ms": 0, "end_ms": 1500}},
        ],
    }


class EditorialValidationTests(unittest.TestCase):
    def test_anchored_audio_and_speech_are_valid(self):
        self.assertEqual(validator.validate(plan()), [])

    def test_clipping_a_word_is_rejected(self):
        data = plan()
        data["clips"][1]["source"]["end_ms"] = 1200
        data["clips"][1]["timeline"]["end_ms"] = 700
        self.assertTrue(any("integralmente preservada" in s for s in validator.validate(data)))

    def test_audio_shift_is_detected_when_the_speaker_is_visible(self):
        data = plan()
        data["clips"][1]["timeline"] = {"start_ms": 200, "end_ms": 1700}
        self.assertTrue(any("áudio deslocado" in s for s in validator.validate(data)))

    def test_valid_j_cut_has_independent_anchored_audio(self):
        data = plan()
        data["clips"][0]["source"]["start_ms"] = 700
        data["clips"][0]["timeline"]["start_ms"] = 200
        self.assertEqual(validator.validate(data), [])

    def test_asset_ids_and_duration_are_checked(self):
        data = plan()
        data["clips"][0]["asset_id"] = "inexistente"
        data["clips"][1]["source"]["end_ms"] = 4000
        data["clips"][1]["timeline"]["end_ms"] = 3500
        errors = validator.validate(data)
        self.assertTrue(any("asset inexistente" in s for s in errors))
        self.assertTrue(any("excede" in s for s in errors))

    def test_structural_invalidity_never_crashes_validator(self):
        data = plan()
        data["clips"][0]["timeline"] = {"start_ms": "zero"}
        self.assertTrue(validator.validate(data))

    def test_independent_audio_over_broll_is_not_forced_to_align(self):
        data = plan()
        data["assets"].append({"id": "broll", "kind": "video", "duration_ms": 2000})
        data["clips"].append({"id": "cobertura", "asset_id": "broll", "track": "v2", "kind": "video", "source": {"start_ms": 0, "end_ms": 1000}, "timeline": {"start_ms": 0, "end_ms": 1000}})
        self.assertEqual(validator.validate(data), [])

    def test_caption_references_existing_speech(self):
        data = plan()
        data["text_layers"] = [{"id": "legenda", "type": "caption", "track": "t1", "text": "não", "timeline": {"start_ms": 500, "end_ms": 900}, "speech_id": "palavra"}]
        self.assertEqual(validator.validate(data), [])
        data["text_layers"][0]["timeline"] = {"start_ms": 1000, "end_ms": 1200}
        self.assertTrue(any("não coincide" in s for s in validator.validate(data)))
        data["text_layers"][0]["speech_id"] = "fala-ausente"
        self.assertTrue(any("fala inexistente" in s for s in validator.validate(data)))

    def test_duplicate_ids_are_rejected(self):
        data = plan()
        data["assets"].append(copy.deepcopy(data["assets"][0]))
        self.assertTrue(any("duplicado" in s for s in validator.validate(data)))


if __name__ == "__main__":
    unittest.main()
