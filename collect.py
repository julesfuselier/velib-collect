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
DATA = Path("data")


def fetch(name, tries=3):
    """Télécharge un flux GBFS, avec 3 essais en cas d'erreur réseau."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(BASE + name, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # réseau, JSON invalide...
            print(f"Essai {i + 1}/{tries} échoué pour {name} : {e}", file=sys.stderr)
            time.sleep(10)
    sys.exit(f"Impossible de récupérer {name}")


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
    rows = []
    for s in status["data"]["stations"]:
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
        ])
    out = DATA / "status" / now.strftime("%Y-%m-%d") / f"{now:%H%M}.csv.gz"
    write_csv_gz(out, ["releve_utc", "station_id", "station_code", "velos_dispo",
                       "velos_meca", "velos_elec", "bornettes_libres", "installee",
                       "location_ok", "retour_ok", "derniere_maj_unix"], rows)
    print(f"{len(rows)} stations enregistrées dans {out}")

    # 2) Caractéristiques des stations (une fois par jour)
    info_path = DATA / "stations" / f"{now:%Y-%m-%d}.csv.gz"
    if not info_path.exists():
        info = fetch("station_information.json")
        write_csv_gz(info_path, ["station_id", "station_code", "nom", "lat", "lon", "capacite"], [
            [s.get("station_id"), s.get("stationCode"), s.get("name"),
             s.get("lat"), s.get("lon"), s.get("capacity")]
            for s in info["data"]["stations"]
        ])
        print(f"Caractéristiques enregistrées dans {info_path}")


if __name__ == "__main__":
    main()
