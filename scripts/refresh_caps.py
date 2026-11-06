#!/usr/bin/env python3
"""Download direct, openly licensed CAP sources; preserve originals and build web copies."""
import datetime,gzip,hashlib,json,re,urllib.request
from pathlib import Path
from shapely import make_valid,set_precision
from shapely.geometry import shape,mapping
from shapely.ops import transform,unary_union
from pyproj import Transformer
R=Path(__file__).resolve().parents[1]
CITIES={'Bologna':'037006','Brescia':'017029','Milano':'015146','Roma':'058091','Napoli':'063049','Torino':'001272'}
BO='https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/codici-avviamento-postale-cap/exports/geojson'
def sha(b):return hashlib.sha256(b).hexdigest()
def polygon(g):
 if not g.is_valid:g=make_valid(g)
 if g.geom_type in ('Polygon','MultiPolygon'):return g
 return unary_union([polygon(x) for x in g.geoms if x.geom_type in ('Polygon','MultiPolygon','GeometryCollection')])
def write(p,d,compressed=False):
 p.parent.mkdir(parents=True,exist_ok=True)
 b=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode()
 p.write_bytes(gzip.compress(b,mtime=0) if compressed else b)
 return {'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def cached(name,url):
 p=R/'.cache'/name;p.parent.mkdir(exist_ok=True)
 if not p.exists():p.write_bytes(urllib.request.urlopen(url,timeout=180).read())
 return p.read_bytes()
def main():
 manifest=json.loads((R/'data/manifest.json').read_text());report=json.loads((R/'reports/validation.json').read_text())
 official=json.loads(gzip.decompress((R/'data/comuni-current.geojson.gz').read_bytes()))
 utm=Transformer.from_crs(4326,32632,always_xy=True).transform;wgs=Transformer.from_crs(32632,4326,always_xy=True).transform
 bounds={f['properties']['com_istat_code']:transform(utm,shape(f['geometry'])) for f in official['features'] if f['properties']['com_istat_code'] in CITIES.values()}
 outputs=[];sources=[];coverage=[];allfeatures=[];discover=[]
 for city,code in CITIES.items():
  slug=city.lower();page='https://zornade.com/mappa-cap/'+slug+'/'
  html=urllib.request.urlopen(page,timeout=60).read().decode()
  links=sorted(set(re.findall(r'https://[^"<>\s]+\.geojson',html)))
  links=[u for u in links if '/citta/'+slug+'.geojson' in u]
  if len(links)!=1 or 'https://creativecommons.org/licenses/by/4.0/' not in html:raise ValueError('Review source or license: '+city)
  zurl=links[0];zb=cached('cap-zornade-'+slug+'.geojson',zurl);zd=json.loads(zb)
  raw=R/('data/cap/source/zornade/'+slug+'.geojson');raw.parent.mkdir(parents=True,exist_ok=True);raw.write_bytes(zb)
  sources.append({'city':city,'provider':'Zornade','page':page,'url':zurl,'file':str(raw.relative_to(R)),'sha256':sha(zb),'bytes':len(zb),'license':'CC-BY-4.0','page_sha256':sha(html.encode()),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'features':len(zd['features'])})
  outputs.append({'path':str(raw.relative_to(R)),'sha256':sha(zb),'bytes':len(zb)})
  municipal=city=='Bologna';url=BO if municipal else zurl
  b=cached('cap-bologna.geojson',url) if municipal else zb
  data=json.loads(b)
  if municipal:
   raw=R/'data/cap/source/comune-bologna/bologna.geojson';raw.parent.mkdir(parents=True,exist_ok=True);raw.write_bytes(b)
   outputs.append({'path':str(raw.relative_to(R)),'sha256':sha(b),'bytes':len(b)})
   sources.append({'city':city,'provider':'Comune di Bologna SIT','page':'https://opendata.comune.bologna.it/explore/dataset/codici-avviamento-postale-cap/','url':url,'file':str(raw.relative_to(R)),'sha256':sha(b),'bytes':len(b),'license':'CC-BY-4.0','features':len(data['features'])})
  features=[];geoms=[];invalid=[];dropped=[];seen=set()
  for f in data['features']:
   p=f['properties'];cap=str(p.get('cap','')).zfill(5)
   if not re.fullmatch(r'\d{5}',cap) or cap in seen:raise ValueError('Invalid/duplicate CAP '+cap)
   seen.add(cap);geom=transform(utm,shape(f['geometry']))
   if not geom.is_valid:invalid.append(cap)
   geom=polygon(polygon(geom).intersection(bounds[code]))
   if geom.is_empty:dropped.append(cap);continue
   geom=polygon(set_precision(transform(wgs,geom.simplify(10,preserve_topology=True)),0.000001))
   if geom.is_empty:raise ValueError('Simplification emptied '+cap)
   geoms.append(transform(utm,geom))
   props={'CAP':cap,'com_istat_code':code,'name':city,'source':'Comune di Bologna SIT' if municipal else 'Zornade (direct download)','license':'CC-BY-4.0','quality':'municipal_open_data' if municipal else 'reconstructed_unverified','source_updated':p.get('ultimo_agg',p.get('ultimo_aggiornamento')),'not_poste_certified':True,'source_url':url,'modifications':'Validity repair where needed; clipped to derived ISTAT 2026 municipality, simplified 10 m, WGS84 precision 6 decimals'}
   features.append({'type':'Feature','id':code+':'+cap,'properties':props,'geometry':mapping(geom)})
  fc={'type':'FeatureCollection','features':features};allfeatures+=features
  outputs.append(write(R/('data/cap/'+slug+'.geojson'),fc));file=write(R/('data/cap/'+slug+'.geojson.gz'),fc,True);outputs.append(file)
  union=unary_union(geoms);den=bounds[code].area
  coverage.append({'city':city,'istat':code,'features':len(features),'unique_caps':len(features),'source_features':len(data['features']),'coverage_of_municipality_pct':round(union.area/den*100,2),'overlap_pct':round((sum(g.area for g in geoms)-union.area)/den*100,3),'geometry_repairs':len(invalid),'repaired_caps':invalid,'dropped_empty_after_clip':dropped,'quality':'municipal_open_data' if municipal else 'reconstructed_unverified','path':file['path'],'license':'CC-BY-4.0','caps':sorted(seen),'source':url})
  print(city,len(features),'coverage',coverage[-1]['coverage_of_municipality_pct'],flush=True)
 outputs.append(write(R/'data/cap/all.geojson',{'type':'FeatureCollection','features':allfeatures}))
 source_manifest={'retrieved_on':'2026-11-06','sources':sources,'selection':'Municipal Bologna preferred; direct Zornade for other cities. Zornade Bologna retained as alternate. Publisher accuracy claims not independently verified.'}
 write(R/'reports/cap-source-discovery.json',source_manifest)
 manifest['sources']=[s for s in manifest['sources'] if not s.get('file','').startswith('cap-')]+sources
 manifest['outputs']=[o for o in manifest['outputs'] if not o['path'].startswith('data/cap/')]+outputs
 manifest['cap_coverage']=coverage;manifest['cap_updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 report['cap_coverage']=coverage
 write(R/'data/manifest.json',manifest);write(R/'reports/validation.json',report)
if __name__=='__main__':main()
