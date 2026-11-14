"""Offline inspection only; no external API requests."""
import argparse,csv,sqlite3,json
from market_classifier import classify_market

def report(db,out):
    rows=[]
    with sqlite3.connect(db) as con:
        for observed,eid,raw in con.execute('SELECT observed_at,event_id,raw_json FROM snapshots'):
            event=json.loads(raw)
            odds=event.get('odds',{})
            if isinstance(odds,dict): labels=list(odds)
            elif isinstance(odds,list): labels=[x.get('marketID',x.get('market','UNKNOWN')) for x in odds if isinstance(x,dict)]
            else: labels=[]
            for label in labels:
                c=classify_market(label)
                rows.append((observed,eid,label,c['category'],c['threshold'],c['period'],c['needs_review']))
    with open(out,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['observed_at','event_id','market_label','category','threshold','period','needs_review']);w.writerows(rows)
    return len(rows)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--csv',default='market_report.csv');a=p.parse_args()
    print(json.dumps({'markets_examined':report(a.db,a.csv),'output':a.csv}))
