"""Offline evidence report: market availability vs parser guesses. Never sends API calls."""
import argparse,collections,csv,json,sqlite3
from market_classifier import classify_market
TARGETS=[('goals',1,'full_match'),('goals',2,'full_match'),('goals',3,'full_match'),('assists',1,'full_match'),('goals',1,'first_half')]

def inspect(db_path,csv_path):
    counts=collections.Counter(); unknown=collections.Counter(); events=set(); snapshots=0
    with sqlite3.connect(db_path) as db:
        for event_id,raw in db.execute('SELECT event_id,raw_json FROM snapshots'):
            snapshots+=1;events.add(event_id)
            event=json.loads(raw); odds=event.get('odds')
            if isinstance(odds,dict): labels=odds.keys()
            elif isinstance(odds,list): labels=[str(x.get('marketID',x.get('market','UNKNOWN'))) for x in odds if isinstance(x,dict)]
            else: labels=[]
            for label in labels:
                c=classify_market(label)
                if c['needs_review']: unknown[str(label)]+=1
                else: counts[(c['category'],c['threshold'],c['period'])]+=1
    with open(csv_path,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['category','threshold','period','classified_market_labels','status'])
        for target in TARGETS:
            w.writerow([*target,counts[target],'LABEL_DETECTED_UNVERIFIED' if counts[target] else 'NOT_OBSERVED'])
    return {'snapshots':snapshots,'unique_events':len(events),'target_market_labels':{'/'.join(map(str,t)):counts[t] for t in TARGETS},'unclassified_labels':unknown.most_common(20),'important':'Label recognition does not verify bookmaker, player, price or availability. No live provider verification.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--csv',default='coverage.csv');a=p.parse_args()
    print(json.dumps(inspect(a.db,a.csv),ensure_ascii=False,indent=2))
