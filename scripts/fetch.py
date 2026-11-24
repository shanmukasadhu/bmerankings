import json, sys, time, urllib.request, urllib.parse, gzip, os
OUT = sys.argv[1]; plan = json.load(open(sys.argv[2]))[sys.argv[3] if len(sys.argv) > 3 else "plan"]
AFF = 'raw_affiliation_strings.search:"biomedical engineering" OR bioengineering'
cost = 0
def get(url):
    for i in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "bme-rankings-builder/1.0"}), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403, 429) and i >= 1: raise SystemExit(f"stopped: HTTP {e.code} (budget?) at {url}")
            time.sleep(3 * (i + 1))
        except Exception as e:
            time.sleep(3 * (i + 1))
    raise SystemExit("failed " + url)
for sid, name, filt in plan:
    path = os.path.join(OUT, sid + ".json.gz")
    if os.path.exists(path): continue
    flt = f"primary_location.source.id:{sid},publication_year:2016-2026,type:article|review" + ("," + AFF if filt else "")
    rows, page = [], 1
    while True:
        d = get("https://api.openalex.org/works?" + urllib.parse.urlencode({"filter": flt, "select": "id,publication_year,authorships", "per_page": 200, "page": page}))
        cost += d["meta"].get("cost_usd") or 0
        for w in d["results"]:
            auth = []
            for a in w["authorships"]:
                insts = [[i["id"].split("/")[-1], i.get("display_name"), i.get("country_code"), i.get("type"), [x.split("/")[-1] for x in i.get("lineage") or []]] for i in a["institutions"]]
                aid = (a.get("author") or {}).get("id")
                auth.append([aid.split("/")[-1] if aid else None, (a.get("author") or {}).get("display_name"), insts])
            rows.append([w["publication_year"], auth])
        if len(d["results"]) < 200 or page >= 50: break
        page += 1
    with gzip.open(path, "wt") as f: json.dump(rows, f)
    print(sid, name, len(rows), "cost", round(cost, 4), flush=True)
print("DONE cost", round(cost, 4))
