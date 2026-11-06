# Data licenses

Administrative sources: ISTAT. Source pages and download hashes are in `data/manifest.json`.
- https://www.istat.it/notizia/confini-delle-unita-amministrative-a-fini-statistici-al-1-gennaio-2018-2/
- https://www.istat.it/classificazione/codici-dei-comuni-delle-province-e-delle-regioni/
- https://creativecommons.org/licenses/by/4.0/

Bologna CAP: Comune di Bologna SIT, CC BY 4.0.
https://opendata.comune.bologna.it/explore/dataset/codici-avviamento-postale-cap/

Other CAP: © Zornade, direct downloads; CC BY 4.0 as declared on each city page retrieved on 2026-11-06.
https://zornade.com/mappa-cap/milano/
https://zornade.com/mappa-cap/brescia/
https://zornade.com/mappa-cap/torino/
https://zornade.com/mappa-cap/roma/
https://zornade.com/mappa-cap/napoli/
https://zornade.com/mappa-cap/bologna/
https://creativecommons.org/licenses/by/4.0/

Zornade Bologna is retained as an alternate original source; the normalized Bologna file uses municipal open data. The prior indirect ODbL distribution is not used for these refreshed CAP files. This is a replacement source, not a relicensing of that distribution.

Geometry transformations: CRS conversion, validity repair, 10 m simplification, clipping to ISTAT municipalities. Derived current municipalities include the two post-January mergers, declared in the manifest and validation report. Reconstructed postal geometry is not certified by Poste Italiane; original source dates are retained per feature.

Historical municipality-CAP associations from matteocontrini/comuni-json: the upstream author does not clarify a data license. See the unchanged `upstream/LICENSE.md`; the MIT license below does not apply to those associations. Dates and verification status are explicitly separate from administrative data.
