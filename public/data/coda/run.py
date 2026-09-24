"""Submit the single frozen computer-10 closing invitation; no retries."""
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
SCRIPTS=Path('C:/Users/Yeste/.agents/skills/computer-10-runpod/scripts')
sys.path.insert(0,str(SCRIPTS))
from common import exact_decoder

RUN='2026-09-24-last-word'
assert exact_decoder(RUN), 'The exact decoder is required.'
subprocess.run([sys.executable,str(SCRIPTS/'turn.py'),'--run',RUN,'--fresh','coda-15001','--seed','15001','--prompt',(HERE/'computer10-prompt.txt').read_text(encoding='utf-8')],check=True)
