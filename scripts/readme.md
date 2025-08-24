# Current script requirements

Currently script does not offer any possibility to download data automatically.
You need to provide the data on your own, e.g. by downloading Lite db1 data with curl:

```bash
curl -o ip2location-lite-db.csv.zip https://download.ip2location.com/lite/IP2LOCATION-LITE-DB1.CSV.ZIP
```

Next, unzip downloaded data:

```bash
unzip ip2location-lite-db.csv.zip 
```

Finally, run the script on unzipped CSV database:

```bash
python3 ip2loc2rsc.py -c PL -o PL-mikrotik-20250825.rsc --list-name "ip-PL" IP2LOCATION-LITE-DB1.CSV
```
