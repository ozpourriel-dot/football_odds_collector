#!/usr/bin/env python3
"""Offline integrity audit. No API calls and no writes to the archive."""
import argparse, hashlib, json, sqlite3

def audit(dbpath):
    result={'snapshots':0,'events':0,'invalid_json':0,'hash_mismatches':0,'duplicates':0,'missing_event_ids':0}
    ids=set(); keys=set()
    with sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True) as db:
        for observed,eid,digest,raw in db.execute('SELECT observed_at,event_id,payload_hash,raw_json FROM snapshots'):
            result['snapshots']+=1; ids.add(eid)
            if not eid: result['missing_event_ids']+=1
            key=(observed,eid,digest)
            if key in keys: result['duplicates']+=1
            keys.add(key)
            if hashlib.sha256(raw.encode()).hexdigest()!=digest: result['hash_mismatches']+=1
            try: json.loads(raw)
            except (ValueError,TypeError): result['invalid_json']+=1
    result['events']=len(ids)
    result['ok']=not any(result[k] for k in ('invalid_json','hash_mismatches','duplicates','missing_event_ids'))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);args=p.parse_args()
    print(json.dumps(audit(args.db),ensure_ascii=False,indent=2))
