import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.capcut_desktop import BridgeError, UnsupportedPlan, call_bridge, translate, write_package


def fixture(media):
    return {
        "version": "1.0",
        "project": {"title": "Teste", "editor": "capcut", "creative_format": "dinamismo"},
        "assets": [{"id": "a", "kind": "video", "duration_ms": 9000, "uri": str(media)}],
        "protected_speech": [{"id": "s", "asset_id": "a", "source": {"start_ms": 1000, "end_ms": 2000}}],
        "clips": [{"id": "c1", "asset_id": "a", "track": "v1", "kind": "video",
                   "source": {"start_ms": 1000, "end_ms": 3000},
                   "timeline": {"start_ms": 0, "end_ms": 2000}, "carries_source_audio": True},
                  {"id": "c2", "asset_id": "a", "track": "v1", "kind": "video",
                   "source": {"start_ms": 4000, "end_ms": 5000},
                   "timeline": {"start_ms": 2000, "end_ms": 3000}, "carries_source_audio": True}],
    }


class FakeSession:
    def __init__(self, error=False):
        self.calls = []
        self.error = error

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return SimpleNamespace(is_error=self.error, content=[SimpleNamespace(type="text", text="erro" if self.error else '{"ok": true}')])


class DesktopBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.media = self.root / "fonte.mp4"
        self.media.write_bytes(b"media local")
        self.plan = fixture(self.media)

    def test_package_maps_source_intervals_and_has_canonical_root(self):
        package = write_package(self.plan, self.root / "novo")
        edit = json.loads((package / "edit-plan.json").read_text())
        handoff = json.loads((package / "mcp-handoff.json").read_text())
        self.assertEqual([(x["sourceStart"], x["duration"]) for x in edit["segments"]], [(1, 2), (4, 1)])
        self.assertEqual(handoff["allowedRoot"], package.as_uri())
        self.assertEqual(edit["id"], handoff["projectID"])
        self.assertEqual(self.media.read_bytes(), b"media local")
        with self.assertRaises(FileExistsError):
            write_package(self.plan, package)

    def test_timeline_gap_or_audio_changes_are_not_silently_dropped(self):
        self.plan["clips"][1]["timeline"] = {"start_ms": 2500, "end_ms": 3500}
        with self.assertRaisesRegex(UnsupportedPlan, "Lacunas"):
            translate(self.plan)
        self.plan["clips"][1]["timeline"] = {"start_ms": 2000, "end_ms": 3000}
        self.plan["clips"][1]["carries_source_audio"] = False
        with self.assertRaisesRegex(UnsupportedPlan, "áudio não solicitado"):
            translate(self.plan)

    def test_editor_and_lettering_require_explicit_supported_route(self):
        self.plan["project"]["editor"] = "davinci"
        with self.assertRaisesRegex(UnsupportedPlan, "CapCut explicitamente"):
            translate(self.plan)
        self.plan["project"]["editor"] = "capcut"
        self.plan["text_layers"] = [{"id": "t", "type": "lettering", "track": "t1", "text": "Oi", "timeline": {"start_ms": 0, "end_ms": 500}}]
        with self.assertRaisesRegex(UnsupportedPlan, "lettering"):
            translate(self.plan)

    def test_missing_or_remote_media_is_rejected(self):
        self.plan["assets"][0]["uri"] = "https://example.com/video.mp4"
        with self.assertRaisesRegex(UnsupportedPlan, "URL remota"):
            translate(self.plan)
        self.plan["assets"][0]["uri"] = str(self.root / "ausente.mp4")
        with self.assertRaisesRegex(UnsupportedPlan, "inacessível"):
            translate(self.plan)

    def test_mcp_commit_is_separate_and_requires_token(self):
        package = write_package(self.plan, self.root / "pacote")
        session = FakeSession()
        with self.assertRaisesRegex(ValueError, "token"):
            asyncio.run(call_bridge(session, "commit", package))
        self.assertEqual(session.calls, [])
        result = asyncio.run(call_bridge(session, "prepare", package, project_name="Meu vídeo"))
        self.assertEqual(result, {"ok": True})
        self.assertEqual(session.calls[0][0], "beditor_capcut_prepare")
        asyncio.run(call_bridge(session, "commit", package, confirmation_token="a" * 64))
        self.assertEqual(session.calls[-1][1]["confirmationToken"], "a" * 64)

    def test_mcp_errors_are_not_reported_as_success(self):
        session = FakeSession(error=True)
        with self.assertRaisesRegex(BridgeError, "erro"):
            asyncio.run(call_bridge(session, "status"))


if __name__ == "__main__":
    unittest.main()
