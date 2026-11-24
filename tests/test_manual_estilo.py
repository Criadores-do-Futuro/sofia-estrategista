import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1] / 'plugin'
spec = importlib.util.spec_from_file_location("manual_estilo", ROOT / "scripts" / "validar_manual_estilo.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def exemplo():
    return {
        "versao": 1,
        "nome": "Referência de entrevista",
        "referencias": [{"id": "ref-1", "fonte": "entrevista.mp4", "duracao_segundos": 12.5}],
        "observacoes": [
            {"id": "corte-1", "aspecto": "ritmo de cortes", "estado": "medido", "descricao": "Corte na troca de plano", "valor": 5.25,
             "evidencias": [{"referencia_id": "ref-1", "inicio_segundos": 5.2, "fim_segundos": 5.3, "modalidade": "video"}]},
            {"id": "fonte-1", "aspecto": "fonte da legenda", "estado": "inferido", "descricao": "Parece uma sans geométrica", "confianca": 0.5,
             "evidencias": [{"referencia_id": "ref-1", "inicio_segundos": 1, "fim_segundos": 3, "modalidade": "video"}]},
            {"id": "efeito-1", "aspecto": "efeito original", "estado": "indisponivel", "descricao": "Não é possível identificar o plugin pela imagem", "evidencias": []},
        ],
    }


class ManualEstiloTest(unittest.TestCase):
    def test_manual_valido_com_evidencias_e_limite_de_duracao(self):
        manual = exemplo()
        manual["observacoes"][0]["evidencias"][0]["fim_segundos"] = 12.5
        self.assertEqual(mod.validar(manual), [])

    def test_evidencias_nao_podem_referir_midia_errada_ou_intervalo_invalido(self):
        manual = exemplo()
        ev = manual["observacoes"][0]["evidencias"][0]
        ev.update(referencia_id="outra", inicio_segundos=7, fim_segundos=6)
        erros = mod.validar(manual)
        self.assertTrue(any("referência inexistente" in e for e in erros))
        self.assertTrue(any("início posterior" in e for e in erros))
        ev.update(referencia_id="ref-1", inicio_segundos=7, fim_segundos=13)
        self.assertTrue(any("excede duração" in e for e in mod.validar(manual)))

    def test_inferencia_precisa_de_evidencia_e_indisponivel_nao_inventa_valor(self):
        manual = exemplo()
        manual["observacoes"][1]["evidencias"] = []
        manual["observacoes"][2]["valor"] = "fonte inventada"
        erros = mod.validar(manual)
        self.assertTrue(any("exige evidência" in e for e in erros))
        self.assertTrue(any("não pode ter valor" in e for e in erros))

    def test_ids_duplicados_e_tempos_booleanos_sao_rejeitados(self):
        manual = exemplo()
        manual["referencias"].append(copy.deepcopy(manual["referencias"][0]))
        manual["observacoes"][1]["id"] = manual["observacoes"][0]["id"]
        manual["observacoes"][0]["evidencias"][0]["inicio_segundos"] = True
        erros = mod.validar(manual)
        self.assertTrue(any("referência duplicada" in e for e in erros))
        self.assertTrue(any("observação duplicada" in e for e in erros))
        self.assertTrue(any("número finito" in e for e in erros))

    def test_cli_rejeita_json_malformado_sem_traceback(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "manual.json"
            arquivo.write_text('{"versao": NaN}', encoding="utf-8")
            resultado = subprocess.run([sys.executable, str(ROOT / "scripts" / "validar_manual_estilo.py"), str(arquivo)], capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 1)
        self.assertFalse(json.loads(resultado.stdout)["valido"])
        self.assertNotIn("Traceback", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
