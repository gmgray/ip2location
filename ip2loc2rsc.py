#!/usr/bin/env python3
import csv
import ipaddress
from pathlib import Path
import argparse

def rows_from_db1(csv_path):
    """
    Oczekuje DB1 IPv4 CSV w formacie:
    "IP_FROM","IP_TO","COUNTRY_CODE"
    z IP w postaci liczb dziesiętnych (bez znaku).
    """
    with open(csv_path, newline='', encoding='utf-8') as f:
        rdr = csv.reader(f)
        for row in rdr:
            if not row or len(row) < 3:
                continue
            try:
                ip_from = int(row[0].strip().strip('"'))
                ip_to   = int(row[1].strip().strip('"'))
                cc      = row[2].strip().strip('"').upper()
            except Exception:
                continue
            yield ip_from, ip_to, cc

def range_to_cidrs(ip_from, ip_to):
    """
    Zamienia zakres numeryczny (inclusive) na listę prefiksów CIDR.
    """
    start = ipaddress.IPv4Address(ip_from)
    end   = ipaddress.IPv4Address(ip_to)
    return list(ipaddress.summarize_address_range(start, end))

def emit_mikrotik_rsc(cidrs, country_code, list_name=None):
    """
    Zwraca tekst .rsc z /ip firewall address-list add ...
    """
    if not list_name:
        list_name = f"Country-{country_code}"
    out = []
    out.append("/ip firewall address-list")
    # opcjonalnie czyścimy starą listę
    out.append(f'remove [find list="{list_name}"]')
    # dodajemy świeże wpisy
    for net in cidrs:
        out.append(f'add list="{list_name}" address={net.exploded}')
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser(
        description="Generuj MikroTik .rsc address-list z IP2Location LITE DB1 (IPv4)."
    )
    ap.add_argument("csv", help="Ścieżka do pliku IP2Location-Lite-DB1.csv (IPv4)")
    ap.add_argument("-c", "--country", required=True, help="Kod kraju ISO2, np. PL")
    ap.add_argument("-o", "--output", default=None, help="Plik wyjściowy .rsc (domyślnie Country-XX.rsc)")
    ap.add_argument("--list-name", default=None, help="Nazwa address-list (domyślnie Country-XX)")
    args = ap.parse_args()

    country = args.country.upper()
    cidrs = []

    for ip_from, ip_to, cc in rows_from_db1(args.csv):
        if cc != country:
            continue
        cidrs.extend(range_to_cidrs(ip_from, ip_to))

    # deduplikacja/normalizacja
    # ipaddress.collapse_addresses scala nachodzące/ciągłe prefiksy
    cidrs = list(ipaddress.collapse_addresses(cidrs))

    # sortowanie dla powtarzalności
    cidrs.sort(key=lambda n: (int(n.network_address), n.prefixlen))

    text = emit_mikrotik_rsc(cidrs, country_code=country, list_name=args.list_name)

    out_path = Path(args.output) if args.output else Path(f"Country-{country}.rsc")
    out_path.write_text(text, encoding="utf-8")

    print(f"Wygenerowano {out_path} ({len(cidrs)} prefiksów CIDR)")

if __name__ == "__main__":
    main()