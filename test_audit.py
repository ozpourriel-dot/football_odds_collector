import json, tempfile, unittest
from pathlib import Path
from collector import store, reserve_call
from audit_archive import audit

class ArchiveAuditTests(unittest.TestCase):
    def test_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'archive.sqlite'
            store({'success':True,'data':[{'eventID':'A','odds':{}}]},path,observed='2026-11-14T12:00:00+00:00')
            self.assertEqual(audit(path)['events'],1)
            self.assertTrue(audit(path)['ok'])
    def test_detect_tampering(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'archive.sqlite'
            store({'success':True,'data':[{'eventID':'A'}]},path)
            with sqlite3.connect(path) as db: db.execute("UPDATE snapshots SET raw_json='{}'")
            self.assertEqual(audit(path)['hash_mismatches'],1)
    def test_daily_cap(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'archive.sqlite'
            reserve_call(path,1)
            with self.assertRaises(RuntimeError): reserve_call(path,1)
if __name__=='__main__': unittest.main()
