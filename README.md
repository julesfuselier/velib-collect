# velib-collect

Collecte automatique de l'état des stations Vélib' Métropole (flux GBFS open data) pour le projet NF21 (UTT, équipe TD1_GR02).

## Fonctionnement

Un workflow GitHub Actions (`.github/workflows/collecte.yml`) lance `collect.py` à intervalle régulier.
Chaque relevé est enregistré dans le dépôt :

- `data/status/AAAA-MM-JJ/HHMM.csv.gz` : état de toutes les stations au moment du relevé (heure UTC)
- `data/stations/AAAA-MM-JJ.csv.gz` : caractéristiques des stations (nom, coordonnées, capacité), une fois par jour

### Colonnes de `status`

| Colonne | Description |
|---|---|
| releve_utc | date et heure du relevé (UTC) |
| station_id, station_code | identifiants de la station |
| velos_dispo | nombre total de vélos disponibles |
| velos_meca, velos_elec | vélos mécaniques / électriques |
| bornettes_libres | places libres pour déposer un vélo |
| installee, location_ok, retour_ok | état de fonctionnement de la station |
| derniere_maj | dernière mise à jour de la station (timestamp Unix pour GBFS, date ISO pour opendata.paris.fr) |
| source | `gbfs` (flux officiel Vélib') ou `opendata.paris.fr` |

## Sources

- Flux GBFS Vélib' Métropole : https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/gbfs.json
- Si le flux GBFS ne répond pas : portail Open Data de la Ville de Paris (jeu velib-disponibilite-en-temps-reel). Dans ce cas `station_id` est vide : utiliser `station_code` pour les jointures.

## Remarques

- Les exécutions programmées de GitHub peuvent être retardées en cas de forte charge : se fier à `releve_utc`.
- Lancer un relevé à la main : onglet Actions → Collecte Velib → Run workflow.
