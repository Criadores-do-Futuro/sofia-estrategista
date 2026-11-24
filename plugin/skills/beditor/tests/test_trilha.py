import sys, tempfile, unittest, wave
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import trilha, acabamento, estilos


class TestTrilha(unittest.TestCase):
    def test_compor_escreve_wav_na_duracao(self):
        with tempfile.TemporaryDirectory() as t:
            saida = Path(t) / "t.wav"
            trilha.compor([{"ateS": 2.0, "clima": "abertura", "cama": "sobe"},
                           {"ateS": 4.0, "clima": "inexistente", "cama": "some"}], 4.0, saida)
            with wave.open(str(saida)) as w:
                self.assertEqual(w.getnchannels(), 2)
                self.assertAlmostEqual(w.getnframes() / w.getframerate(), 4.0, places=2)

    def test_compor_aceita_estilo_e_cai_no_padrao_sem_id_conhecido(self):
        with tempfile.TemporaryDirectory() as t:
            for estilo in ("vox", "editorial", "punk"):
                saida = Path(t) / f"{estilo}.wav"
                trilha.compor([{"ateS": 1.0, "clima": "tensao", "cama": "mantem"}], 1.0,
                              saida, estilo)
                self.assertTrue(saida.exists())

    def test_envelope_vox_sobe_mais_rapido_que_editorial(self):
        mov = {"acorde": [110.0], "ganho": 0.15, "pulso": 60, "brilho": 0.1, "tensao": 0.1}
        vox, _ = trilha.render(dict(mov), 1.0, estilos.MUSICA["vox"])
        edt, _ = trilha.render(dict(mov), 1.0, estilos.MUSICA["editorial"])
        # 0,3 s de ataque: o envelope mais curto do vox ja chegou mais perto do
        # pico do que o sustentado do editorial no mesmo instante
        i = int(0.3 * trilha.SR)
        self.assertGreater(abs(vox[i]), abs(edt[i]))

    def test_volume_da_cama(self):
        # voz -14, cama -26.2 -> 18 dB abaixo = -32 -> ganho 10^((-32+26.2)/20)
        self.assertAlmostEqual(acabamento.volume_da_cama_por_lufs(-14.0, -26.2), 0.513, places=2)


def _rms_db(*args, af=None):
    import subprocess
    medida = "astats=measure_overall=RMS_level:measure_perchannel=0"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args, "-af", f"{af},{medida}" if af else medida,
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return float([l for l in r.stderr.splitlines() if "RMS level dB" in l][-1].split()[-1])


class TestCamaAbreEspacoParaAVoz(unittest.TestCase):
    def test_low_pass_derruba_a_faixa_da_consoante(self):
        tom = lambda hz, af: _rms_db("-f", "lavfi", "-i", f"sine=f={hz}:d=1", af=af)
        # 500 Hz passa quase inteiro; 6 kHz (meio da faixa 3-7 kHz) cai >= 20 dB
        self.assertGreater(tom(500, acabamento.CAMA) - tom(500, None), -1.5)
        self.assertLess(tom(6000, acabamento.CAMA) - tom(6000, None), -20)

    def test_ducking_abaixa_a_cama_so_enquanto_ha_voz(self):
        import subprocess
        with tempfile.TemporaryDirectory() as t:
            saida = Path(t) / "m.wav"
            # voz: 1 s de fala no nivel de -14 LUFS (~-12 dB RMS) e 1 s de silencio; cama: tom constante
            grafo = ("[0:a]volume=3[v];[1:a]volume=0.5[m];"
                     + acabamento.mistura_voz_cama("[v]", "[m]", "[mix]") + ";[mix]anull[a]")
            subprocess.run(["ffmpeg", "-y", "-v", "error",
                            "-f", "lavfi", "-i", "sine=f=4000:d=1,apad=pad_dur=1",
                            "-f", "lavfi", "-i", "sine=f=200:d=2",
                            "-filter_complex", grafo, "-map", "[a]", str(saida)], check=True)
            # so a cama (200 Hz) importa: tira a voz com um low pass
            com_voz = _rms_db("-t", "0.9", "-i", str(saida), af="lowpass=f=300,lowpass=f=300,lowpass=f=300")
            sem_voz = _rms_db("-ss", "1.8", "-i", str(saida), af="lowpass=f=300,lowpass=f=300,lowpass=f=300")
        self.assertLess(com_voz, sem_voz - 2)


if __name__ == "__main__":
    unittest.main()
