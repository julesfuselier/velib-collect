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
| derniere_maj_unix | dernière mise à jour de la station (timestamp Unix) |

## Source

Flux GBFS Vélib' Métropole : https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/gbfs.json

## Remarques

- Les exécutions programmées de GitHub peuvent être retardées en cas de forte charge : se fier à `releve_utc`.
- Lancer un relevé à la main : onglet Actions → Collecte Velib → Run workflow.
