"""Frozen wrapper: submit one adaptive turn or all eight precommitted fresh probes."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = Path('C:/Users/Yeste/.agents/skills/computer-10-runpod/scripts')
RUN = '2026-09-23-borrowed-notebook-b'
assert importlib.util.find_spec('tokenizers'), 'Exact decoder is required.'
sys.path.insert(0, str(SCRIPTS))
from common import exact_decoder

def submit(*args):
    assert exact_decoder(RUN), 'Abort: no exact decoder.'
    subprocess.run([sys.executable, str(SCRIPTS/'turn.py'), '--run', RUN, *args], check=True)

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--prompt')
    ap.add_argument('--probes', action='store_true')
    a=ap.parse_args()
    assert bool(a.prompt) != a.probes
    if a.probes:
        for p in json.loads((HERE/'probes.json').read_text(encoding='utf-8')):
            submit('--fresh',p['id'],'--seed',str(p['seed']),'--prompt',p['prompt'])
    else:
        submit('--session','notebook-session','--seed-base','9301','--prompt',a.prompt)
