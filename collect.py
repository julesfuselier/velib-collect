"""Relève l'état de toutes les stations Vélib' (flux GBFS) et l'enregistre.

Chaque exécution écrit un fichier compressé :
    data/status/AAAA-MM-JJ/HHMM.csv.gz   (heure UTC du relevé)
Une fois par jour, il enregistre aussi les caractéristiques des stations :
    data/stations/AAAA-MM-JJ.csv.gz

Aucune dépendance : uniquement la bibliothèque standard de Python.
"""
import csv
import gzip
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/"
# Autre source officielle des mêmes données : portail Open Data de la Ville de Paris
PARIS = ("https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
         "velib-disponibilite-en-temps-reel/exports/json")
DATA = Path("data")
# On identifie clairement le projet auprès des serveurs
HEADERS = {
    "User-Agent": "velib-collect/1.0 (projet etudiant UTT NF21; "
                  "https://github.com/julesfuselier/velib-collect)",
    "Accept": "application/json",
}


def get_json(url, tries=3):
    """Télécharge un JSON, avec 3 essais. Renvoie None en cas d'échec."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # réseau, 403, JSON invalide...
            print(f"Essai {i + 1}/{tries} échoué pour {url} : {e}", file=sys.stderr)
            time.sleep(5)
    return None


def fetch(name):
    """Flux GBFS officiel (station_status.json ou station_information.json)."""
    return get_json(BASE + name)


def yes(v):
    """Convertit 'OUI'/'NON', True/False ou 1/0 en 1/0."""
    if isinstance(v, str):
        return 1 if v.strip().upper() in ("OUI", "YES", "TRUE", "1") else 0
    return 1 if v else 0


def from_paris(now):
    """Portail Open Data de la Ville de Paris. Renvoie (lignes_status, lignes_stations)."""
    data = get_json(PARIS)
    if not data:
        return None, None
    status, info = [], []
    for s in data:
        geo = s.get("coordonnees_geo") or {}
        status.append([
            now.isoformat(timespec="seconds"), "", s.get("stationcode"),
            s.get("numbikesavailable"), s.get("mechanical"), s.get("ebike"),
            s.get("numdocksavailable"), yes(s.get("is_installed")),
            yes(s.get("is_renting")), yes(s.get("is_returning")), s.get("duedate"),
            "opendata.paris.fr",
        ])
        info.append(["", s.get("stationcode"), s.get("name"), geo.get("lat"),
                     geo.get("lon"), s.get("capacity")])
    return status, info


def bikes_by_type(station):
    """Sépare les vélos mécaniques et électriques."""
    meca = ebike = 0
    for t in station.get("num_bikes_available_types", []):
        meca += t.get("mechanical", 0)
        ebike += t.get("ebike", 0)
    return meca, ebike


def write_csv_gz(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    now = datetime.now(timezone.utc)

    # 1) État des stations (à chaque exécution)
    status = fetch("station_status.json")
    rows, paris_info = [], None
    if status is None:
        print("Flux GBFS indisponible : utilisation de opendata.paris.fr", file=sys.stderr)
        rows, paris_info = from_paris(now)
        if not rows:
            sys.exit("Aucune source disponible pour ce relevé")
    for s in (status["data"]["stations"] if status else []):
        meca, ebike = bikes_by_type(s)
        rows.append([
            now.isoformat(timespec="seconds"),
            s.get("station_id"),
            s.get("stationCode"),
            s.get("num_bikes_available"),
            meca,
            ebike,
            s.get("num_docks_available"),
            s.get("is_installed"),
            s.get("is_renting"),
            s.get("is_returning"),
            s.get("last_reported"),
            "gbfs",
        ])
    out = DATA / "status" / now.strftime("%Y-%m-%d") / f"{now:%H%M}.csv.gz"
    write_csv_gz(out, ["releve_utc", "station_id", "station_code", "velos_dispo",
                       "velos_meca", "velos_elec", "bornettes_libres", "installee",
                       "location_ok", "retour_ok", "derniere_maj", "source"], rows)
    print(f"{len(rows)} stations enregistrées dans {out}")

    # 2) Caractéristiques des stations (une fois par jour)
    info_path = DATA / "stations" / f"{now:%Y-%m-%d}.csv.gz"
    if not info_path.exists():
        header = ["station_id", "station_code", "nom", "lat", "lon", "capacite"]
        info = None if paris_info else fetch("station_information.json")
        if info:
            lines = [[s.get("station_id"), s.get("stationCode"), s.get("name"),
                      s.get("lat"), s.get("lon"), s.get("capacity")]
                     for s in info["data"]["stations"]]
        else:
            lines = paris_info or from_paris(now)[1]
        if lines:
            write_csv_gz(info_path, header, lines)
            print(f"Caractéristiques enregistrées dans {info_path}")


if __name__ == "__main__":
    main()
