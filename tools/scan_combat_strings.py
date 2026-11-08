"""Read-only native string inventory. Names are leads, not control-flow proof."""
import hashlib
import argparse
import json
import re
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game-root', type=Path, required=True)
parser.add_argument('--output', type=Path, default=repo / '.local/evidence')
args = parser.parse_args()
target = args.game_root.resolve() / 'platform/steam/PBZ.exe'
data = target.read_bytes()
pattern = re.compile(r'(damage|friendlyfire|friendly.fire|hostile|teamid|faction|attitude|health|hitresult|multiplayer|replicat|netdriver|playercontroller|playercharacter)', re.I)
rows = []
for encoding, regex in [('ascii', rb'[\x20-\x7e]{5,240}'), ('utf-16le', rb'(?:[\x20-\x7e]\x00){5,240}')]:
    for match in re.finditer(regex, data):
        value = match.group().decode(encoding)
        if pattern.search(value):
            rows.append({'file_offset': hex(match.start()), 'encoding': encoding, 'text': value})
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
(out / 'native-combat-strings.json').write_text(json.dumps({
    'target': str(target), 'sha256': hashlib.sha256(data).hexdigest(),
    'scope': 'Printable ASCII and ASCII-subset UTF-16LE strings matching combat/network terms; no disassembly or runtime verification.',
    'matches': rows,
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'matches': len(rows), 'evidence': str(out / 'native-combat-strings.json')}))
for row in rows:
    if re.search(r'PBZ|Friendly|Faction|Attitude|TeamId|Hostile', row['text'], re.I):
        print(row['file_offset'], row['text'])
