#!/usr/bin/env python3
"""Offline inventory of market keys; does not assume a vendor-specific odds schema."""
import argparse, csv, json, sqlite3
from collections import Counter


def inventory(dbpath):
    counts=Counter()
    with sqlite3.connect(dbpath) as db:
        for (raw,) in db.execute('SELECT raw_json FROM snapshots'):
            event=json.loads(raw)
            odds=event.get('odds')
            if isinstance(odds,dict):
                for key in odds:
                    counts[str(key)]+=1
            elif isinstance(odds,list):
                for entry in odds:
                    if isinstance(entry,dict):
                        counts[str(entry.get('marketID',entry.get('market','UNKNOWN')))]+=1
    return counts

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--db',default='odds_archive.sqlite')
    p.add_argument('--csv',default='market_inventory.csv')
    args=p.parse_args()
    counts=inventory(args.db)
    with open(args.csv,'w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['market_key','snapshot_occurrences'])
        w.writerows(counts.most_common())
    print(json.dumps({'distinct_market_keys':len(counts),'output':args.csv}))
