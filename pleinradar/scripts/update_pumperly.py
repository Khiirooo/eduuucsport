#!/usr/bin/env python3
"""Import verified, recently sourced Belgian retail fuel prices from Pumperly.
Pumperly provides a public no-key API, but no CORS: server-side import only.
Public readability is not a licence to redistribute third-party commercial data.
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "stations.json"
FUELS = {"E10":"e10","E5_98":"e5_98","B7":"b7","B7_PREMIUM":"b7_premium","LPG":"lpg","CNG":"cng"}
BBOX = "2.4,49.4,6.6,51.6"
NOW = datetime.now(timezone.utc)

def get_features(fuel):
    q = urllib.parse.urlencode({"bbox": BBOX, "fuel": fuel})
    req=urllib.request.Request("https://pumperly.com/api/stations?"+q,headers={"User-Agent":"PleinRadar/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=70) as res:
        if res.status != 200: raise ValueError("HTTP status "+str(res.status))
        data = json.load(res)
    if not isinstance(data,dict) or data.get("type") != "FeatureCollection" or not isinstance(data.get("features"),list):
        raise ValueError("Bad GeoJSON "+fuel)
    return data["features"]

def parse_feature(f, fuel):
    p=f.get("properties") or {}
    c=(f.get("geometry") or {}).get("coordinates") or []
    if p.get("country") != "BE" or p.get("fuelType") != fuel or p.get("currency") != "EUR" or len(c)<2: return None
    try:
        lon,lat=map(float,c[:2]); price=float(p["price"])
        stamp=datetime.fromisoformat(p["reportedAt"].replace("Z","+00:00"))
    except (TypeError,KeyError,ValueError,AttributeError): return None
    if not (2.4<=lon<=6.6 and 49.4<=lat<=51.6 and 0.3<=price<=(20 if fuel=="CNG" else 4.5)):return None
    if stamp.tzinfo is None or not (NOW-timedelta(hours=48)<=stamp<=NOW+timedelta(hours=1)):return None
    sid=str(p.get("externalId") or "").strip()
    if not sid:return None
    return sid,lon,lat,price,stamp.isoformat().replace("+00:00","Z"),p

def main():
    stations={}
    successful=0
    errors=[]
    for upstream,local in FUELS.items():
        try: feats=get_features(upstream)
        except Exception as exc:
            errors.append(upstream+": "+str(exc))
            if upstream in ("E10","B7"):raise
            continue
        valid=0
        for f in feats:
            item=parse_feature(f,upstream)
            if item is None:continue
            sid,lon,lat,price,stamp,p=item
            key="pumperly-be-"+sid
            s=stations.get(key)
            if s is None:
                s={"id":key,"name":str(p.get("name") or "Station-service")[:120],"brand":str(p.get("brand") or "")[:90],
                   "address":str(p.get("address") or "")[:180],"city":str(p.get("city") or "")[:100],
                   "postalCode":"","lat":round(lat,6),"lon":round(lon,6),"prices":{},"priceUpdatedAtByFuel":{}}
                stations[key]=s
            elif abs(s["lat"]-lat)>.004 or abs(s["lon"]-lon)>.004:continue
            s["prices"][local]=round(price,3)
            s["priceUpdatedAtByFuel"][local]=stamp
            valid+=1
        successful+=valid
        print(upstream, len(feats), "features", valid, "valid Belgian prices",flush=True)
    e10=sum("e10" in x["prices"] for x in stations.values())
    if e10<20 or len(stations)<20:
        raise RuntimeError("Refuse missing/unverified prices: E10="+str(e10)+" stations="+str(len(stations))+"; "+str(errors))
    for s in stations.values():
        s["priceUpdatedAt"]=max(s["priceUpdatedAtByFuel"].values())
    data={"updatedAt":NOW.isoformat().replace("+00:00","Z"),
          "source":"Pumperly / ANWB — prix indicatifs","sourceUrl":"https://pumperly.com/",
          "sourceNote":"Horodatage du fournisseur, non vérifié à la pompe",
          "stations":sorted(stations.values(),key=lambda s:(s["city"].lower(),s["name"].lower(),s["id"]))}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    temp=OUT.with_suffix(".tmp")
    temp.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    temp.replace(OUT)
    print("Imported",len(stations),"stations;",successful,"fuel prices",flush=True)

if __name__=="__main__":main()
