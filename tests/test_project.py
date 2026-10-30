from src.generator import build
from src.analyze import evaluate
import hashlib

def test_reproducibility(tmp_path):
 a=tmp_path/'a';b=tmp_path/'b';build(a,7,9,50);build(b,7,9,50)
 for p in a.iterdir():assert p.read_bytes()==(b/p.name).read_bytes()

def test_full_anomalies(tmp_path):
 build(tmp_path,20,9,100)
 result=evaluate(tmp_path)
 assert result['ground_truth']>=8
 assert result['true_positive']>=7
