import copy, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import publicacao as pub

BOM = {
    "video": "master.mp4",
    "palavraChave": "iPhone Duo",
    "capa": {"t": 0.5, "linhas": ["iPhone Duo", "para criador"], "destaque": "Duo"},
    "redes": {
        "youtube": {"titulo": "iPhone Duo: o celular que todo criador vai querer",
                    "descricao": "iPhone Duo para criador de conteúdo: câmera traseira com prévia.",
                    "tags": ["iphone duo", "criador de conteúdo"]},
        "instagram": {"legenda": "iPhone Duo mudou como eu gravo. #iphoneduo #criador #reels"},
        "tiktok": {"legenda": "iPhone Duo para quem grava sozinho #iphoneduo #criador #dicas"},
    },
    "agendamento": {"quando": "2026-09-12T19:00", "fuso": "America/Argentina/Cordoba",
                    "contas": {"instagram": "acc_ig"}},
}


class TestPublicacao(unittest.TestCase):
    def test_bom_passa_sem_erro(self):
        erros, avisos = pub.validar(BOM)
        self.assertEqual(erros, [])
        self.assertEqual(avisos, [])

    def test_limite_da_rede_e_erro(self):
        d = copy.deepcopy(BOM)
        d["redes"]["youtube"]["titulo"] = "iPhone Duo " + "x" * 100
        self.assertTrue(any("limite é 100" in e for e in pub.validar(d)[0]))

    def test_palavra_chave_fora_da_primeira_linha_e_aviso(self):
        d = copy.deepcopy(BOM)
        d["redes"]["instagram"]["legenda"] = "a" * 130 + " iPhone Duo"
        self.assertTrue(any("instagram" in a and "palavra-chave" in a for a in pub.validar(d)[1]))

    def test_capa_com_texto_demais_e_erro(self):
        d = copy.deepcopy(BOM)
        d["capa"]["linhas"] = ["um dois tres quatro", "cinco seis sete oito nove"]
        self.assertTrue(any("capa" in e for e in pub.validar(d)[0]))

    def test_um_post_para_todas_as_redes(self):
        corpo = pub.payload_zernio(BOM)
        self.assertEqual([p["platform"] for p in corpo["platforms"]], ["youtube", "instagram", "tiktok"])
        self.assertEqual(len(corpo["mediaItems"]), 1)            # um upload, todas as redes
        yt = corpo["platforms"][0]
        self.assertEqual(yt["platformSpecificData"]["title"], BOM["redes"]["youtube"]["titulo"])
        ig = corpo["platforms"][1]
        self.assertNotIn("customContent", ig)                    # é o texto principal
        self.assertIn("instagramThumbnail", ig["platformSpecificData"])
        self.assertIn("customContent", corpo["platforms"][2])
        self.assertEqual(ig["accountId"], "acc_ig")
        self.assertEqual(corpo["tags"], BOM["redes"]["youtube"]["tags"])

    def test_capa_sai_em_1080x1920_com_texto_na_area_segura(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            video = t / "master.mp4"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                            "testsrc=s=1080x1920:r=30:d=1", "-c:v", "libx264", "-preset",
                            "ultrafast", "-pix_fmt", "yuv420p", str(video)], check=True)
            info = pub.desenhar_capa(video, BOM["capa"], t / "capa.jpg")
            self.assertTrue(info["cabe"])
            self.assertLess(info["bytes"], 2 * 1024 * 1024)
            self.assertEqual(Image.open(t / "capa.jpg").size, (1080, 1920))


if __name__ == "__main__":
    unittest.main()
