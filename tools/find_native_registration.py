"""Inspect PE literal-pointer references; candidates require disassembly."""
import json
import hashlib
import argparse
import struct
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game-root', type=Path, required=True)
parser.add_argument('--output', type=Path, default=repo / '.local/evidence')
args = parser.parse_args()
data = (args.game_root.resolve() / 'platform/steam/PBZ.exe').read_bytes()
pe = struct.unpack_from('<I', data, 0x3c)[0]
count = struct.unpack_from('<H', data, pe + 6)[0]
optional_size = struct.unpack_from('<H', data, pe + 20)[0]
base = struct.unpack_from('<Q', data, pe + 24 + 24)[0]
sections = []
for i in range(count):
    off = pe + 24 + optional_size + i * 40
    name = data[off:off+8].rstrip(b'\0').decode()
    size, rva, raw_size, raw = struct.unpack_from('<IIII', data, off+8)
    flags = struct.unpack_from('<I', data, off+36)[0]
    sections.append(dict(name=name, rva=rva, raw=raw, raw_size=raw_size, size=size, flags=flags))

def va(off):
    for s in sections:
        if s['raw'] <= off < s['raw'] + s['raw_size']:
            return base + s['rva'] + off - s['raw']

names = ['SetFactionRelationOverride', 'SetFaction', 'FilterTargetsByFactionRelation',
         'TakeDamage', 'GetHealthAttribute', 'IsValidTargetFactionRelation',
         'GetFactionRelation', 'BPI_TakeDamage']
rows = []
for name in names:
    for encoding in ['ascii', 'utf-16le']:
        needle = name.encode(encoding) + (b'\0' if encoding == 'ascii' else b'\0\0')
        start = 0
        while (offset := data.find(needle, start)) >= 0:
            start = offset + 1
            address = va(offset)
            if address is None:
                continue
            pointer = struct.pack('<Q', address)
            refs = []
            pos = 0
            while (pos := data.find(pointer, pos)) >= 0:
                refs.append({'file_offset':hex(pos), 'va':hex(va(pos) or 0),
                             'next_qword':hex(struct.unpack_from('<Q', data, pos+8)[0]),
                             'previous_qword':hex(struct.unpack_from('<Q', data, pos-8)[0])})
                pos += 1
            rows.append({'name':name, 'encoding':encoding, 'file_offset':hex(offset),
                         'va':hex(address), 'pointer_references':refs})
args.output.mkdir(parents=True, exist_ok=True)
out = args.output / 'native-registration-candidates.json'
out.write_text(json.dumps({'sha256':hashlib.sha256(data).hexdigest(), 'image_base':hex(base), 'sections':sections, 'candidates':rows},indent=2),encoding='utf-8')
for row in rows:
    if row['pointer_references']:
        print(json.dumps(row))
