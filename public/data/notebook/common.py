"""Shared paths and helpers for the computer-10 RunPod scripts. Standard library only."""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
BUNDLE = SKILL/'bundle'
RUNPODCTL = os.environ.get('RUNPODCTL', 'D:/Interiority-V1/tools/runpodctl-2.14.0/runpodctl.exe')
SSH_KEY = str(Path.home()/'.runpod/ssh/runpodctl-ssh-key')
TEMPLATE_ID = os.environ.get('COMPUTER10_TEMPLATE', 'sbj4xwvjpu')
RUNS = Path(os.environ.get('COMPUTER10_RUNS', 'D:/Interiority-V1/computer-10/runs'))
REMOTE_PORT = 8767
STOPS = ['\n\n**User:**', '\n\n**Model C:**']


def now():
    return datetime.now(timezone.utc).isoformat()


def runpodctl(*args):
    env = {**os.environ, 'MSYS_NO_PATHCONV': '1'}
    out = subprocess.run([RUNPODCTL, *args], capture_output=True, text=True, encoding='utf-8', env=env)
    if out.returncode:
        raise RuntimeError(f'runpodctl {" ".join(args)} failed: {out.stderr or out.stdout}')
    return json.loads(out.stdout) if out.stdout.strip() else None


def ssh_base(info):
    return ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=15',
            '-i', SSH_KEY]


def ssh(info, command, timeout=120):
    return subprocess.run(['ssh', *ssh_base(info), '-p', str(info['port']), f"root@{info['ip']}", command],
                          capture_output=True, text=True, encoding='utf-8', timeout=timeout)


def scp(info, source, target, timeout=600):
    out = subprocess.run(['scp', '-q', *ssh_base(info), '-P', str(info['port']), source, target],
                         capture_output=True, text=True, timeout=timeout)
    if out.returncode:
        raise RuntimeError(f'scp failed: {out.stderr}')


def run_dir(name):
    return RUNS/name


def load_rental(name):
    return json.loads((run_dir(name)/'rental.json').read_text(encoding='utf-8'))


def save_rental(name, rental):
    path = run_dir(name)/'rental.json'
    path.write_text(json.dumps(rental, indent=2)+'\n', encoding='utf-8', newline='\n')


def exact_decoder(name):
    """Decode token IDs without clean_up_tokenization_spaces, which drops spaces before quotation marks."""
    try:
        from tokenizers import Tokenizer
    except ImportError:
        return None
    for path in [run_dir(name)/'tokenizer.json', Path('D:/Interiority-V1/computer-10/model/tokenizer.json')]:
        if path.exists():
            tok = Tokenizer.from_file(str(path))

            def decode(ids):
                text = tok.decode(ids, skip_special_tokens=True)
                for marker in STOPS:
                    text = text.split(marker, 1)[0]
                return text.strip()
            return decode
    return None
