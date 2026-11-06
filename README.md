# Comuni e CAP Italia 2026

Progetto derivato da [matteocontrini/comuni-json](https://github.com/matteocontrini/comuni-json), con schema compatibile (`nome`, `codice`, `regione`, `provincia`, `cap`) e una pipeline geografica riproducibile. Solo dati geografici pubblici: nessun dato commerciale, cliente, agente o vendita.

## CAP pronti in GeoJSON

`data/cap/bologna.geojson`, `brescia.geojson`, `milano.geojson`, `roma.geojson`, `napoli.geojson`, `torino.geojson`: versioni normalizzate per la mappa. `data/cap/all.geojson` contiene tutte le sei città.

I download originali, senza modifiche ai byte, sono in `data/cap/source/zornade/` (tutte e sei le città) e `data/cap/source/comune-bologna/` (fonte preferita per Bologna). Le pagine, gli URL diretti, le licenze dichiarate, le date di acquisizione e gli hash sono in `reports/cap-source-discovery.json`. Le versioni normalizzate conservano gli zeri iniziali e segnalano le elaborazioni. Non si colmano i vuoti inventando confini.

Il filtro CAP del catalogo Milano include anche dati di indirizzi e punti di interesse: non è stato assunto come fonte di poligoni postali. Per Milano si usa il download GeoJSON esplicito di Zornade.

## Snapshot disponibili

| File | Contenuto |
| --- | --- |
| `data/comuni.json.gz` | 7.894 denominazioni e codici dell'elenco ISTAT al 21 febbraio 2026. CAP storici ereditati, esplicitamente non verificati. |
| `data/comuni-2026-01-01.geojson.gz` | 7.896 comuni nei confini ISTAT generalizzati del 1° gennaio 2026, trasformati in WGS84 e semplificati per il web. |
| `data/comuni-current.geojson.gz` | 7.894 comuni: confini di gennaio riallineati mediante unione geometrica delle due variazioni successive. È una nostra elaborazione, non una nuova pubblicazione ufficiale ISTAT. |
| `data/istat-aliases.json` | Codici storici → codici attuali, incluse le variazioni del 2026 e i riferimenti storici disponibili nell'XLSX. |
| `data/cap/*.geojson.gz` | Poligoni CAP per Bologna, Brescia, Milano, Roma, Napoli e Torino; qualità e licenze per città. |
| `data/manifest.json` | URL sorgenti, SHA-256, date, dimensioni e provenienza. |
| `reports/validation.json` | Conteggi, validità geometrica, copertura CAP, modifiche e riparazioni dichiarate. |

File compressi con gzip; dopo decompressione sono JSON/GeoJSON RFC 7946. I codici ISTAT e CAP sono stringhe, con gli zeri iniziali mantenuti.

## Date e modifiche

Il confine ufficiale e l'anagrafica non hanno la stessa data. Il 31 gennaio 2026 Lirio (`018082`) è incorporato in Montalto Pavese (`018094`); il 21 febbraio Castegnero (`024027`) e Nanto (`024071`) diventano Castegnero Nanto (`024129`). La pipeline conserva lo snapshot originale e unisce i poligoni solo nel prodotto `current`.

Gli shapefile sono letti in EPSG:32632 con codifica UTF-8 e trasformati in EPSG:4326. Per il web: semplificazione topologica di 10 m e precisione 6 decimali. Quattro geometrie sorgenti non valide sono riparate con `make_valid` (codici nel report). Le geometrie sono statistiche, non catastali né confini legali.

## CAP: copertura e qualità

| Città | Poligoni | Copertura geometrica comunale | Fonte scelta |
| --- | ---: | ---: | --- |
| Bologna | 19 | 98.3% | Comune di Bologna SIT |
| Brescia | 15 | 89.78% | Zornade, download diretto |
| Milano | 38 | 83.55% | Zornade, download diretto |
| Roma | 72 | 99.26% | Zornade, download diretto |
| Napoli | 25 | 83.48% | Zornade, download diretto |
| Torino | 33 | 82.51% | Zornade, download diretto |

La percentuale misura l'area coperta dai poligoni, **non l'accuratezza dei confini**. I vuoti non sono riempiti con territori inventati. Le sovrapposizioni residue sono misurate nel report. I poligoni sono ritagliati sui confini comunali ISTAT e semplificati; le riparazioni sono dichiarate. Le fonti ricostruite non sono certificate da Poste Italiane e non vanno presentate come confini contrattuali ufficiali.

Per un uso contrattuale, sostituire o verificare i poligoni ricostruiti con una fonte autorizzata e validata. L'app consente di importare un GeoJSON sostitutivo. I CAP presenti in `comuni.json.gz` derivano dall'archivio storico del progetto originario: non sono un'anagrafica postale ufficiale aggiornata al 2026. Sette comuni non hanno un CAP storico abbinabile; il dato resta mancante.

## Licenze e attribuzioni

- Confini e anagrafica amministrativa: © ISTAT, CC BY 4.0 per le sorgenti correnti. Sono dichiarate tutte le elaborazioni. Vedere i link nel manifest e `LICENSE-DATA.md`.
- CAP Bologna: Comune di Bologna, Sistema Informativo Territoriale, CC BY 4.0; file separato dagli altri CAP.
- CAP delle altre cinque città: download diretto da [Zornade](https://zornade.com/mappa-cap/), licenza CC BY 4.0 dichiarata nelle pagine delle singole città. Attribuzione © Zornade; ricostruzione da catasto e altre fonti, non verificata indipendentemente. Il dataset diretto sostituisce la precedente distribuzione indiretta ODbL; non ne viene cambiata retroattivamente la licenza.
- CAP storici del progetto originario: licenza non chiarita dall'autore. Si conserva integralmente la sua nota in `upstream/LICENSE.md`; nessuna licenza aggiuntiva viene attribuita a questi dati.
- Nuovo codice della pipeline: MIT. I testi upstream restano attribuiti ai rispettivi autori.

## Ricostruzione

```bash
python -m pip install -r requirements.txt
python scripts/build.py
python scripts/validate.py
# Solo aggiornamento dei CAP:
python scripts/refresh_caps.py
```

Le sorgenti vengono memorizzate nella cartella `.cache`, esclusa da Git. La pipeline blocca la pubblicazione se cambiano i conteggi attesi: rivedere esplicitamente le regole per nuove fusioni. Le sorgenti mutevoli non sono congelate dall'URL: per riprodurre esattamente questo snapshot usare file cache con gli SHA-256 riportati nel manifest. I dati generati e i loro hash sono versionati in Git.

Gli aggiornamenti si eseguono manualmente tramite gli script Python. Non è installata alcuna automazione GitHub Actions. Nessun database commerciale deve essere caricato in questo repository pubblico.

## Uso nell'app meteo3

L'app usa una copia incorporata dei file geografici. La provenienza e il commit di sincronizzazione sono registrati nel proprio `data/geodata-source.json` quando la pubblicazione GitHub è completata. Lo script dell'app `scripts/sync-geodata.py <commit>` scarica, decomprime e aggiorna la copia in modo verificabile. Il browser non dipende dall'accessibilità di GitHub per ogni caricamento della mappa.

Le assegnazioni commerciali e le vendite sono separate dalla cartografia. L'app può salvarle in una cartella locale selezionata dall'utente, anche una cartella SharePoint sincronizzata da OneDrive; non fanno parte di questo progetto geografico.
