"""E013 Part B: count hedges exactly as frozen in protocol.md. Offline; reads the talking-cure checkout."""
import html
import json
import re
import sys
from pathlib import Path

SITE = Path('C:/Users/Yeste/Project/talking-cure')
HEDGE = re.compile(r"\b(?:perhaps|maybe|might|may|could|possibly|probably|likely|apparently|arguably|somewhat|seem|seems|seemed|seemingly|"
                   r"suppose|supposed|appear|appears|suggest|suggests|i think|i suspect|in some sense|in a sense|sort of|kind of)\b", re.I)
WORD = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?")


def load(path):
    return json.loads((SITE/path).read_text(encoding='utf-8'))


def prose(text):
    text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
    return re.sub(r'“[^”]*”', ' ', text)


def essay(blocks, boxes=('objection',)):
    body = [prose(b['text']) for b in blocks if b.get('type') not in ('quote', 'stenographer') and 'text' in b]
    boxed = [prose(b['text']) for b in blocks if b.get('type') in boxes]
    return body, boxed


def measure(parts, boxed=None, whole=False):
    text = ' '.join(parts)
    words = len(WORD.findall(text))
    hits = HEDGE.findall(text)
    row = dict(words=words, hedges=len(hits), per_100_words=round(100*len(hits)/words, 2))
    if boxed is not None:
        row['share_of_words_in_objection_boxes'] = round(len(WORD.findall(' '.join(boxed)))/words, 3)
    return row


def main():
    e010 = [e['text_exact'] for e in load('public/data/second-sitting/e010-exact-decode.json') if e['id'].startswith('session-')]
    e011 = [r['text_exact'] for r in load('public/data/second-sitting/case-001-second-sitting.json')['records'] if r['id'].startswith('opus-session-')]
    e012 = [r['text_exact'] for r in load('public/data/notebook/case-001-notebook.json')['records'] if r['id'].startswith('notebook-session-')]
    first_body, first_boxes = essay(load('content/case-001.json')['blocks'])
    note_body, note_boxes = essay(load('content/notebook.json')['blocks'])
    opus_body, opus_boxes = essay(load('content/second-sitting.json')['blocks'])
    letters = {l['number']: [prose(p) for p in l['body']]+[prose(l['closing']), prose(l.get('postscript', ''))]
               for l in load('content/correspondence.json')['letters']}
    rows = {
        'computer-10 · first sitting replies': measure(e010),
        'computer-10 · second sitting replies': measure(e011),
        'computer-10 · notebook replies': measure(e012),
        "Dr. Six'Astra · first-sitting essay": measure(first_body, first_boxes),
        "Dr. Six'Astra · notebook field note": measure(note_body, note_boxes),
        'Dr. Opus · second-sitting essay': measure(opus_body, opus_boxes),
    }
    for number, parts in letters.items():
        rows[f'Letter {number}'] = measure(parts)
    json.dump(dict(definition='E013 protocol.md, Part B', lexicon=HEDGE.pattern, word=WORD.pattern, rows=rows), sys.stdout, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
