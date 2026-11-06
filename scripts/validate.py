import gzip,json,hashlib
from pathlib import Path
from shapely.geometry import shape
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'data/manifest.json').read_text())
for item in manifest['outputs']:
 p=R/item['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],p
current=json.loads(gzip.decompress((R/'data/comuni-current.geojson.gz').read_bytes()))
names=json.loads(gzip.decompress((R/'data/comuni.json.gz').read_bytes()))
assert len(current['features'])==len(names)==7894
assert {f['properties']['com_istat_code'] for f in current['features']}=={c['codice'] for c in names}
assert all(len(c['codice'])==6 and c['codice'].isdigit() for c in names)
assert all(shape(f['geometry']).is_valid and not shape(f['geometry']).is_empty for f in current['features'])
report=json.loads((R/'reports/validation.json').read_text());assert len(report['cap_coverage'])==6
for city in report['cap_coverage']:
 d=json.loads(gzip.decompress((R/city['path']).read_bytes()))
 assert len(d['features'])==city['features']>0
 for f in d['features']:
  assert len(f['properties']['CAP'])==5 and f['properties']['CAP'].isdigit()
  assert f['properties']['com_istat_code']==city['istat']
  assert shape(f['geometry']).is_valid and not shape(f['geometry']).is_empty
assert next(c for c in names if c['codice']=='001001')['nome']=='Agliè'
assert next(c for c in names if c['codice']=='024129')['nome']=='Castegnero Nanto'
assert not any(c['codice'] in ['018082','024027','024071'] for c in names)
print('Validated: 7894 current municipalities, six CAP cities, valid geometries, hashes and UTF-8 names.')
