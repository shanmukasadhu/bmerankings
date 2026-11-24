import json, sys, time, urllib.request, urllib.parse, gzip, os
OUT = sys.argv[1]
SOURCES = ["S2764624792","S141152059","S5240358","S163807576","S173145877","S161954266","S26035906",
 "S58069681","S116571295","S32898093","S98183460","S181675524","S11710983","S116836101","S156181945","S2495854775"]
cost = 0
def get(url):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "bme-rankings-builder/1.0"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            print("retry", e, file=sys.stderr); time.sleep(3*(i+1))
    raise SystemExit("failed " + url)
for s in SOURCES:
    path = os.path.join(OUT, s + ".json.gz")
    if os.path.exists(path): continue
    rows = []; done = False
    for yr, page in ((y, p) for y in range(2016, 2027) for p in range(1, 51)):
        if page > 1 and done: continue
        done = False
        q = urllib.parse.urlencode({"filter": f"primary_location.source.id:{s},publication_year:{yr},type:article|review",
            "select": "id,publication_year,authorships", "per_page": 200, "page": page})
        d = get("https://api.openalex.org/works?" + q)
        cost += d["meta"].get("cost_usd") or 0
        for w in d["results"]:
            auth = []
            for a in w["authorships"]:
                insts = [[i["id"].split("/")[-1], i.get("display_name"), i.get("country_code"), i.get("type"), [x.split("/")[-1] for x in i.get("lineage") or []]] for i in a["institutions"]]
                aid = (a.get("author") or {}).get("id")
                auth.append([aid.split("/")[-1] if aid else None, (a.get("author") or {}).get("display_name"), insts])
            rows.append([w["publication_year"], auth])
        if len(d["results"]) < 200: done = True
    with gzip.open(path, "wt") as f: json.dump(rows, f)
    print(s, len(rows), "cost so far", round(cost, 4), flush=True)
