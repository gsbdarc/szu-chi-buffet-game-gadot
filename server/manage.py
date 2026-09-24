#!/usr/bin/env python3
"""Local researcher maintenance: consistent SQLite backups and exports."""
import argparse
import json
from pathlib import Path
import sqlite3
from buffet_server import ROOT, Store, export_csv

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['backup','export-json','export-csv'])
    parser.add_argument('output')
    parser.add_argument('--db', default=str(ROOT/'server/data/buffet.sqlite3'))
    args = parser.parse_args()
    source = Path(args.db).resolve()
    if not source.is_file(): parser.error('Database does not exist')
    target = Path(args.output).resolve()
    if target.exists(): parser.error('Output already exists; choose a new filename')
    target.parent.mkdir(parents=True, exist_ok=True)
    if args.action == 'backup':
        origin = sqlite3.connect('file:'+str(source)+'?mode=ro',uri=True)
        destination = sqlite3.connect(str(target))
        try:
            origin.backup(destination)
            if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok': raise RuntimeError('Backup integrity check failed')
        finally:
            origin.close();destination.close()
    else:
        sessions = Store(source).export()
        target.write_text(json.dumps({'schemaVersion':1,'sessions':sessions},indent=2) if args.action=='export-json' else export_csv(sessions),encoding='utf-8')
    print('Wrote '+str(target))

if __name__=='__main__':main()
