#!/usr/bin/env python3
import csv
import ipaddress
from pathlib import Path
import argparse

def rows_from_db1(csv_path):
    """
    Expects DB1 IPv4 CSV with fields
    "IP_FROM","IP_TO","COUNTRY_CODE"
    where IP* is an integer coded value (unsigned)
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
    Changes numeric range (inclusive) to CIDR prefix list.
    """
    start = ipaddress.IPv4Address(ip_from)
    end   = ipaddress.IPv4Address(ip_to)
    return list(ipaddress.summarize_address_range(start, end))

def emit_mikrotik_rsc(cidrs, country_code, list_name=None):
    """
    Returns .rsc MikroTik script file with firewall-compatible 
    address list definition
    """
    if not list_name:
        list_name = f"Country-{country_code}"
    out = []
    out.append("/ip firewall address-list")
    out.append(f'remove [find list="{list_name}"]')
    # new entries
    for net in cidrs:
        out.append(f'add list="{list_name}" address={net.exploded}')
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser(
        description="Create MikroTik rsc script from IP2Location Lite DB1 (IPv4) CSV file"
    )
    ap.add_argument("csv", help="CSV file location")
    ap.add_argument("-c", "--country", required=True, help="ISO 02 Country Code, eg. PL")
    ap.add_argument("-o", "--output", default=None, help="Output .rsc script file name (default Country-XX.rsc)")
    ap.add_argument("--list-name", default=None, help="Address-list name (default Country-XX)")
    args = ap.parse_args()

    country = args.country.upper()
    cidrs = []

    for ip_from, ip_to, cc in rows_from_db1(args.csv):
        if cc != country:
            continue
        cidrs.extend(range_to_cidrs(ip_from, ip_to))

    # dedup/normalize
    # ipaddress.collapse_addresses merges overlapping / continuous ranges
    cidrs = list(ipaddress.collapse_addresses(cidrs))

    # 
    cidrs.sort(key=lambda n: (int(n.network_address), n.prefixlen))

    text = emit_mikrotik_rsc(cidrs, country_code=country, list_name=args.list_name)

    out_path = Path(args.output) if args.output else Path(f"Country-{country}.rsc")
    out_path.write_text(text, encoding="utf-8")

    print(f"Created {out_path} ({len(cidrs)} CIDR prefixes)")

if __name__ == "__main__":
    main()