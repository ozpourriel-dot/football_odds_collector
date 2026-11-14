#!/usr/bin/env python3
"""SportsGameOdds v2: conservative one-page snapshot collector.
No existing Football Data Center resource is accessed.
"""
import argparse, datetime as dt, hashlib, json, os, sqlite3, sys, urllib.error, urllib.parse, urllib.request, csv
from pathlib import Path

API='https://api.sportsgameodds.com/v2/events'

def store(payload, dbpath, observed=None):
    if not isinstance(payload,dict) or payload.get('success') is not True or not isinstance(payload.get('data'),list):
        raise ValueError('Unexpected API response: success=true and data list required')
    observed=observed or dt.datetime.now(dt.timezone.utc).isoformat()
    path=Path(dbpath); path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, event_id TEXT NOT NULL, payload_hash TEXT NOT NULL, raw_json TEXT NOT NULL, UNIQUE(observed_at,event_id,payload_hash))')
        db.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_event ON snapshots(event_id, observed_at)')
        n=0
        for event in payload['data']:
            if not isinstance(event,dict): continue
            eid=event.get('eventID')
            if eid is None: continue
            raw=json.dumps(event,sort_keys=True,ensure_ascii=False,separators=(',',':'))
            h=hashlib.sha256(raw.encode()).hexdigest()
            cur=db.execute('INSERT OR IGNORE INTO snapshots(observed_at,event_id,payload_hash,raw_json) VALUES(?,?,?,?)',(observed,str(eid),h,raw))
            n+=cur.rowcount
    return n,len(payload['data'])

def reserve_call(dbpath, cap):
    day=dt.datetime.now(dt.timezone.utc).date().isoformat()
    path=Path(dbpath); path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path,timeout=30) as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS api_calls (day TEXT PRIMARY KEY, reserved INTEGER NOT NULL)')
        used=db.execute('SELECT reserved FROM api_calls WHERE day=?',(day,)).fetchone()
        if used and used[0]>=cap:
            db.rollback()
            raise RuntimeError('Local daily API call cap reached; no request sent')
        db.execute('INSERT INTO api_calls(day,reserved) VALUES(?,1) ON CONFLICT(day) DO UPDATE SET reserved=reserved+1',(day,))
        db.commit()

def export_snapshots(dbpath, csvpath):
    with sqlite3.connect(dbpath) as db, open(csvpath,'w',encoding='utf-8',newline='') as out:
        writer=csv.writer(out)
        writer.writerow(['observed_at','event_id','payload_hash','raw_json'])
        writer.writerows(db.execute('SELECT observed_at,event_id,payload_hash,raw_json FROM snapshots ORDER BY observed_at,event_id'))

def fetch(key,limit):
    params=urllib.parse.urlencode({'sportID':'SOCCER','oddsAvailable':'true','limit':limit})
    req=urllib.request.Request(API+'?'+params,headers={'x-api-key':key,'Accept':'application/json','User-Agent':'FDC-OddsCollector/0.1'})
    with urllib.request.urlopen(req,timeout=25) as response:
        return json.load(response)

def main():
    p=argparse.ArgumentParser(description='Conservative SportsGameOdds snapshot collector')
    p.add_argument('--fixture',help='Read a local JSON response instead of calling API')
    p.add_argument('--db',default='odds_archive.sqlite')
    p.add_argument('--limit',type=int,default=5)
    p.add_argument('--daily-cap',type=int,default=2)
    p.add_argument('--export-csv')
    args=p.parse_args()
    if not 1<=args.limit<=10: p.error('--limit must be 1..10')
    if not 1<=args.daily_cap<=100: p.error('--daily-cap must be 1..100')
    if args.export_csv:
        export_snapshots(args.db,args.export_csv)
        print('Export completed without an API call')
        return
    try:
        if args.fixture:
            with open(args.fixture,encoding='utf-8') as f: data=json.load(f)
        else:
            key=os.getenv('SPORTSGAMEODDS_API_KEY')
            if not key: p.error('Set SPORTSGAMEODDS_API_KEY securely in the environment')
            reserve_call(args.db,args.daily_cap)
            data=fetch(key,args.limit)
        n,total=store(data,args.db)
        print(json.dumps({'status':'ok','events_received':total,'snapshots_inserted':n,'has_next_cursor':bool(data.get('nextCursor')),'database':args.db}))
    except urllib.error.HTTPError as e:
        print(f'HTTP error {e.code} (no API key printed)',file=sys.stderr); sys.exit(2)
    except Exception as e:
        print(f'Collector error: {type(e).__name__}: {e}',file=sys.stderr); sys.exit(2)

if __name__=='__main__': main()
