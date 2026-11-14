import tempfile,unittest,sqlite3,json,os
from market_classifier import classify_market
from coverage_report import inspect
class CoverageTests(unittest.TestCase):
 def test_plus_thresholds(self):
  for n in (1,2,3): self.assertEqual(classify_market(f'Player Goals {n}+')['threshold'],n)
 def test_no_team_or_under(self):
  for label in ('Team Goals Over 2.5','Player Goals Under 1.5','No Goalscorer'):
   self.assertTrue(classify_market(label)['needs_review'])
 def test_conflict(self): self.assertTrue(classify_market('Player Goals 2+ 3+')['needs_review'])
 def test_offline_coverage(self):
  with tempfile.TemporaryDirectory() as d:
   db=os.path.join(d,'a.db');csv=os.path.join(d,'out.csv')
   with sqlite3.connect(db) as con:
    con.execute('CREATE TABLE snapshots(event_id TEXT,raw_json TEXT)')
    con.execute('INSERT INTO snapshots VALUES(?,?)',('fake',json.dumps({'odds':{'Player Goals 2+':{}}})))
   r=inspect(db,csv)
   self.assertEqual(r['target_market_labels']['goals/2/full_match'],1)
   self.assertEqual(r['target_market_labels']['goals/3/full_match'],0)
if __name__=='__main__': unittest.main()
