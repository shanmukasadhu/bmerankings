import json, sys, gzip, os
from collections import defaultdict
RAW, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "config.py")).read())
_vol = json.load(open(os.path.join(HERE, "volumes.json")))
_plan = json.load(open(os.path.join(HERE, "plan.json")))
FILTERED = {sid for sid, _, f in _plan["plan"] if f}
_ids = {**_vol["ids"], **EXTRA_IDS}
VENUES = [(_ids[full], short, ai, full) for ai, A in enumerate(AREAS) for full, short in A[3]
          if os.path.exists(os.path.join(sys.argv[1], _ids[full] + ".json.gz"))]
PENDING = [full for A in AREAS for full, _ in A[3] if not os.path.exists(os.path.join(sys.argv[1], _ids[full] + ".json.gz"))]
YEARS = list(range(2016, 2027))
import re, glob
inst_name, inst_cc, inst_type = {}, {}, {}
for f in glob.glob(os.path.join(RAW, "*.json.gz")):
    for _, authorships in json.load(gzip.open(f, "rt")):
        for _, _, insts in authorships:
            for iid, name, cc, typ, _ in insts:
                if name: inst_name.setdefault(iid, name); inst_cc.setdefault(iid, cc); inst_type.setdefault(iid, typ)
SUBUNIT = re.compile(r"medic|department|graduate school|school of|college of|faculty of|health science", re.I)
def roots_for(iid, name, lineage):
    anc = [x for x in lineage if x != iid and inst_type.get(x) == "education"]
    if anc and name and SUBUNIT.search(name): return anc
    return [iid]
inst = defaultdict(float)            # (root, area, yi) -> adj
auth = defaultdict(lambda: [0.0, 0])  # (aid, root, area, yi) -> [adj, raw]
auth_name = {}
for ai, (sid, _, _, _) in enumerate(VENUES):
    if True:
        for year, authorships in json.load(gzip.open(os.path.join(RAW, sid + ".json.gz"), "rt")):
            n = len(authorships)
            if not n or year not in YEARS: continue
            yi = YEARS.index(year)
            for aid, aname, insts in authorships:
                roots = []
                for iid, name, cc, typ, lineage in insts:
                    if typ != "education": continue
                    for root in roots_for(iid, name, lineage):
                        if root not in roots: roots.append(root)
                for r in roots:
                    share = 1.0 / n / len(roots)
                    inst[(r, ai, yi)] += share
                    if aid:
                        e = auth[(aid, r, ai, yi)]; e[0] += share; e[1] += 1
                        auth_name[aid] = aname
# institution totals; keep those with >= 3 adjusted pubs overall
tot = defaultdict(float)
for (r, a, y), v in inst.items(): tot[r] += v
keep = sorted([r for r, v in tot.items() if v >= 3 and r in inst_name], key=lambda r: -tot[r])
idx = {r: i for i, r in enumerate(keep)}
inst_rows = [[inst_name[r], inst_cc.get(r) or "", r, []] for r in keep]
for (r, a, y), v in inst.items():
    if r in idx: inst_rows[idx[r]][3].append([a, y, round(v, 3)])
# authors: keep author-institution pairs with >= 1.0 adjusted overall
atot = defaultdict(float)
for (aid, r, a, y), (v, c) in auth.items(): atot[(aid, r)] += v
amap, arows = {}, []
for (aid, r, a, y), (v, c) in auth.items():
    if r not in idx or atot[(aid, r)] < 1.0: continue
    k = (aid, r)
    if k not in amap:
        amap[k] = len(arows); arows.append([auth_name[aid], idx[r], aid, []])
    arows[amap[k]][3].append([a, y, c, round(v, 3)])
missing = [r for r in tot if r not in inst_name and tot[r] >= 3]
meta = {"groups": [{"key": k, "label": l, "short": sh, "desc": d} for k, l, sh, d in GROUPS],
        "areas": [{"key": k, "name": n, "group": g} for k, n, g, _ in AREAS], "pending": PENDING, "extra": list(EXTRA_IDS),
        "venues": [{"name": sh, "full": full, "area": ai, "f": sid in FILTERED} for sid, sh, ai, full in VENUES], "years": YEARS}
json.dump({"meta": meta, "insts": inst_rows}, open(os.path.join(OUT, "institutions.json"), "w"), separators=(",", ":"))
json.dump(arows, open(os.path.join(OUT, "authors.json"), "w"), separators=(",", ":"))
print("insts", len(inst_rows), "authors", len(arows), "missing names", len(missing), missing[:10])
print([(inst_name[r], round(tot[r])) for r in keep[:25]])
