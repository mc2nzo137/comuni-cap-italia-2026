#!/usr/bin/env python3
"""Build reproducible public geography snapshots. Never includes commercial data."""
import argparse,datetime,gzip,hashlib,json,shutil,urllib.request,zipfile,subprocess
from pathlib import Path
import geopandas as gpd,openpyxl
from shapely import make_valid,set_precision
from shapely.geometry import shape,mapping,Polygon,MultiPolygon
from shapely.ops import unary_union,transform
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'istat-2026.zip':'https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/2026/Limiti01012026_g.zip',
 'elenco-comuni.xlsx':'https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.xlsx',
 'legacy.json':'https://raw.githubusercontent.com/matteocontrini/comuni-json/master/comuni.json',
}
CITIES={'Bologna':'037006','Brescia':'017029','Milano':'015146','Roma':'058091','Napoli':'063049','Torino':'001272'}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(path,obj,compress=True):
 path.parent.mkdir(parents=True,exist_ok=True)
 raw=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
 path.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0) if compress else raw)
 return {'path':str(path.relative_to(ROOT)), 'sha256':digest(path),'bytes':path.stat().st_size}
def polygon(g):
 if not g.is_valid:g=make_valid(g)
 if g.geom_type in ['Polygon','MultiPolygon']:return g
 parts=[polygon(x) for x in g.geoms if x.geom_type in ['Polygon','MultiPolygon','GeometryCollection']]
 return unary_union([x for x in parts if not x.is_empty])

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--cache',default=str(ROOT/'.cache'));args=parser.parse_args();cache=Path(args.cache);cache.mkdir(parents=True,exist_ok=True)
 for name,url in SOURCES.items():
  p=cache/name
  if not p.exists():
   print('Downloading',name,flush=True)
   with urllib.request.urlopen(url,timeout=180) as res,p.open('wb') as out:shutil.copyfileobj(res,out)
 with zipfile.ZipFile(cache/'istat-2026.zip') as z:z.extractall(cache/'istat')
 shp=next((cache/'istat').glob('Com*/*.shp'));df=gpd.read_file(shp,encoding='utf-8');assert df.crs.to_epsg()==32632
 if len(df)!=7896:raise ValueError('Unexpected January snapshot; review source changes')
 records=[r for r in list(openpyxl.load_workbook(cache/'elenco-comuni.xlsx',read_only=True,data_only=True).active.values)[1:] if r[4]]
 if len(records)!=7894:raise ValueError('Anagrafica changed: review merger rules before building')
 legacy=json.loads((cache/'legacy.json').read_text());legacyByCode={c['codice']:c for c in legacy};legacyByCat={c['codiceCatastale']:c for c in legacy}
 official={str(r[4]).zfill(6):r for r in records};sourceGeom={r.PRO_COM_T:polygon(r.geometry) for _,r in df.iterrows()};rawRepairs=[r.PRO_COM_T for _,r in df.iterrows() if not r.geometry.is_valid]
 currentGeom=dict(sourceGeom);nameToCode={r[6]:k for k,r in official.items()};mergers=[{'date':'2026-01-31','target':nameToCode['Montalto Pavese'],'sources':[nameToCode['Montalto Pavese'],'018082']},{'date':'2026-02-21','target':'024129','sources':['024027','024071']}]
 for change in mergers:
  geom=polygon(unary_union([currentGeom.pop(k) for k in change['sources']]))
  currentGeom[change['target']]=geom
 if set(currentGeom)!=set(official):raise ValueError('Geometries and denomination register do not match')
 aliases={};comuni=[]
 for code,r in sorted(official.items()):
  old=legacyByCat.get(r[20],legacyByCode.get(code,{}));caps=old.get('cap',[])
  for change in mergers:
   if code==change['target']:caps=sorted(set(caps+[c for k in change['sources'] for c in legacyByCode.get(k,{}).get('cap',[])]))
  comune={'nome':r[6],'codice':code,'zona':{'codice':str(r[8]),'nome':r[9]},'regione':{'codice':str(r[0]).zfill(2),'nome':r[10]},'provincia':{'codice':str(r[1]).zfill(3),'nome':r[11]},'sigla':r[14],'codiceCatastale':r[20],'cap':caps,'cap_status':'legacy_unverified' if caps else 'missing','names_reference_date':'2026-02-21'}
  comuni.append(comune)
  for previous in [old.get('codice')]+[str(v).zfill(6) for v in r[16:20] if v]:
   if previous and previous!=code:aliases[previous]=code
 for change in mergers:
  for previous in change['sources']:
   if previous!=change['target']:aliases[previous]=change['target']
 toWGS=Transformer.from_crs(32632,4326,always_xy=True).transform;toUTM=Transformer.from_crs(4326,32632,always_xy=True).transform
 def feature(code,geom,p):
  simplified=polygon(geom.simplify(10,preserve_topology=True));wgs=polygon(set_precision(transform(toWGS,simplified),0.000001))
  return {'type':'Feature','id':code,'properties':p,'geometry':mapping(wgs)}
 byCode={c['codice']:c for c in comuni}
 currentFeatures=[feature(k,g,{'com_istat_code':k,'name':byCode[k]['nome'],'prov_name':byCode[k]['provincia']['nome'],'reg_name':byCode[k]['regione']['nome'],'boundary_source_date':'2026-01-01','names_reference_date':'2026-02-21','derived_after_merger':any(m['target']==k for m in mergers)}) for k,g in sorted(currentGeom.items())]
 originalFeatures=[feature(r.PRO_COM_T,sourceGeom[r.PRO_COM_T],{'com_istat_code':r.PRO_COM_T,'name':r.COMUNE,'boundary_source_date':'2026-01-01'}) for _,r in df.iterrows()]
 outputs=[dump(ROOT/'data/comuni.json.gz',comuni),dump(ROOT/'data/comuni-current.geojson.gz',{'type':'FeatureCollection','features':currentFeatures}),dump(ROOT/'data/comuni-2026-01-01.geojson.gz',{'type':'FeatureCollection','features':originalFeatures}),dump(ROOT/'data/istat-aliases.json',aliases,False)]
 capReports=[]
 report={'january_count':len(df),'current_count':len(comuni),'current_features':len(currentFeatures),'valid_geometries':all(shape(f['geometry']).is_valid for f in currentFeatures),'unique_codes':len(set(c['codice'] for c in comuni)),'original_geometry_repairs':rawRepairs,'mergers':mergers,'cap_coverage':capReports,'legacy_cap_missing':sum(not c['cap'] for c in comuni),'web_simplification_m':10}
 dump(ROOT/'reports/validation.json',report,False)
 manifest={'schema':1,'built_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'boundary_source_date':'2026-01-01','names_reference_date':'2026-02-21','upstream':'https://github.com/matteocontrini/comuni-json','sources':[{'url':url,'sha256':digest(cache/name),'file':name} for name,url in SOURCES.items()],'outputs':outputs,'cap_coverage':capReports,'notes':['January original retained. Current geometry is a derived union for the two subsequent changes.','Legacy municipality-CAP mappings are not an official 2026 postal register.','Reconstructed CAP polygons must be validated before contractual boundary decisions.']}
 dump(ROOT/'data/manifest.json',manifest,False)
 subprocess.run([__import__("sys").executable,str(ROOT/"scripts/refresh_caps.py")],check=True)
 print((ROOT/"reports/validation.json").read_text())
if __name__=='__main__':main()
