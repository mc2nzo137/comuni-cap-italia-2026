# Pubblicazione e aggiornamenti

Repository: https://github.com/mc2nzo137/comuni-cap-italia-2026

Il progetto contiene esclusivamente cartografia pubblica e codice di elaborazione. Non caricare TERRITORIO, STRUTTURA, VENDITE o dati di clienti e personale.

I file GeoJSON pronti sono in data/cap; i download originali sono in data/cap/source. Fonti, licenze, hash e controlli sono documentati in README.md, LICENSE-DATA.md, data/manifest.json e reports/validation.json.

Per aggiornare soltanto i CAP: installare requirements.txt, quindi eseguire python scripts/refresh_caps.py e python scripts/validate.py. Eliminare dalla cache solo i download che si desidera aggiornare; la cache conserva lo snapshot di origine per la riproducibilità. Per una ricostruzione amministrativa completa usare scripts/build.py, rivedendo le regole se l'elenco ISTAT è cambiato.
