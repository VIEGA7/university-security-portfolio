"""Reconstructed from storage lab 4 / image18.jpg; no destructive delete_many.

Input: local MITRE ATT&CK STIX bundle, not downloaded automatically.
Run --dry-run to validate without pymongo or a database.
"""
import argparse
import json
import os
from pathlib import Path


def objects(path):
    bundle = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(bundle, dict) or bundle.get('type') != 'bundle':
        raise ValueError('Expected a STIX bundle')
    entries = bundle.get('objects')
    if not isinstance(entries, list):
        raise ValueError('bundle.objects must be a list')
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str) or not entry['id']:
            raise ValueError('Each object requires a STIX id')
    return entries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    entries = objects(args.bundle)
    if args.dry_run:
        print(f'{len(entries)} objects validated; no database changes')
    else:
        from pymongo import MongoClient, ReplaceOne
        password = os.environ['MONGO_PASSWORD']
        with MongoClient('127.0.0.1',27010,username='portfolio_admin',password=password,
                         authSource='admin',serverSelectionTimeoutMS=5000) as client:
            collection = client['portfolio_lab']['mitre_attack']
            # Keep distinct STIX versions; rerunning a bundle replaces the same versions.
            collection.create_index([('id',1),('modified',1)],unique=True)
            for start in range(0,len(entries),500):
                batch = [ReplaceOne({'id':e['id'],'modified':e.get('modified')},e,upsert=True)
                         for e in entries[start:start+500]]
                collection.bulk_write(batch,ordered=False)
            print(f'{len(entries)} objects processed; total documents={collection.count_documents({})}')
