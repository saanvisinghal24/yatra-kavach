"""Run browser tests with private root configuration; app must be running."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from runtime import ROOT,load_environment,npm,run
if __name__=='__main__':
    run([npm(),'run','test:browser'],cwd=ROOT/'web',env=load_environment())
