import json, sqlite3, tempfile, unittest
from pathlib import Path
from collector import store, reserve_call, export_snapshots
from inspect_markets import inventory

class CollectorTests(unittest.TestCase):
    def test_snapshot_and_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'archive.sqlite'
            payload={'success':True,'data':[{'eventID':'A','odds':{'sample':{'byBookmaker':{'x':{'odds':'2.5'}}}}}]}
            self.assertEqual(store(payload,db,'2026-11-14T12:00:00+00:00'),(1,1))
            self.assertEqual(store(payload,db,'2026-11-14T12:00:00+00:00'),(0,1))
            self.assertEqual(store(payload,db,'2026-11-14T12:05:00+00:00'),(1,1))
            with sqlite3.connect(db) as c:
                self.assertEqual(c.execute('select count(*) from snapshots').fetchone()[0],2)
    def test_cap_and_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'archive.sqlite'
            reserve_call(db,1)
            with self.assertRaises(RuntimeError): reserve_call(db,1)
            store({'success':True,'data':[{'eventID':'A'}]},db)
            output=Path(tmp)/'archive.csv'
            export_snapshots(db,output)
            self.assertIn('event_id',output.read_text())
    def test_market_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'archive.sqlite'
            store({'success':True,'data':[{'eventID':'A','odds':{'anytime_goalscorer':{'player':'A'}}}]},db)
            self.assertEqual(inventory(db)['anytime_goalscorer'],1)
    def test_reject_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):store({'data':[]},Path(tmp)/'x.db')

if __name__=='__main__':unittest.main()
