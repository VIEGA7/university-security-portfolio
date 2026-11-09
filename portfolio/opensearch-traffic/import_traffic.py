"""Reconstruction of storage lab 5 importer, without pandas/opensearch-py.

Strict conversions; deterministic IDs; bounded batches; bulk-item error checks.
The local compose intentionally disables authentication and binds only loopback.
"""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import ipaddress
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

FIELDS = {
    'frame.time_epoch': 'date', 'frame.number': 'long', 'frame.len': 'integer',
    'ip.src': 'ip', 'ip.dst': 'ip', 'frame.protocols': 'keyword',
    'tcp.srcport': 'integer', 'tcp.dstport': 'integer',
    'udp.srcport': 'integer', 'udp.dstport': 'integer', 'http.host': 'keyword',
    'tls.handshake.extensions_server_name': 'keyword', 'dns.qry.name': 'keyword',
    'http.request.method': 'keyword', 'http.response.code': 'integer',
    'tcp.flags': 'keyword', 'eth.src': 'keyword',
}


def nested_set(target, dotted, value):
    parts = dotted.split('.')
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def convert_row(row):
    if None in row or any(value is None for value in row.values()):
        raise ValueError('CSV column count does not match the header')
    if not row.get('frame.time_epoch', '').strip():
        raise ValueError('frame.time_epoch is required; no fabricated current timestamps')
    document = {}
    for field, kind in FIELDS.items():
        text = (row.get(field) or '').strip()
        if not text:
            continue
        values = [x.strip() for x in text.split(',') if x.strip()]
        if kind == 'date':
            if len(values) != 1:
                raise ValueError('one frame.time_epoch value expected')
            try:
                number = Decimal(values[0])
            except InvalidOperation as error:
                raise ValueError('invalid epoch timestamp') from error
            if not number.is_finite() or not math.isfinite(float(number)):
                raise ValueError('timestamp must be finite')
            value = float(number)
        elif kind in ('integer', 'long'):
            converted = [int(x) for x in values]
            if any(x < 0 for x in converted):
                raise ValueError(f'{field} must be nonnegative')
            if field.endswith('port') and any(x > 65535 for x in converted):
                raise ValueError('port outside 0..65535')
            value = converted[0] if len(converted) == 1 else converted
        elif kind == 'ip':
            converted = [str(ipaddress.ip_address(x)) for x in values]
            value = converted[0] if len(converted) == 1 else converted
        else:
            value = values[0] if len(values) == 1 else values
        nested_set(document, field, value)
    return document


def template():
    properties = {}
    for field, kind in FIELDS.items():
        node = properties
        parts = field.split('.')
        for part in parts[:-1]:
            node = node.setdefault(part, {'properties': {}})['properties']
        node[parts[-1]] = {'type': kind}
        if kind == 'date':
            node[parts[-1]]['format'] = 'epoch_second'
    return {'index_patterns': ['packets-mbm-*'], 'template': {
        'settings': {'number_of_shards': 1, 'number_of_replicas': 0},
        'mappings': {'dynamic': 'strict', 'properties': properties}}}


def bulk_lines(document, index, capture_id, row_number):
    # Preserve identical packets at different row numbers; rerunning the same capture is idempotent.
    digest = hashlib.sha256(f'{capture_id}:{row_number}'.encode()).hexdigest()
    return (json.dumps({'index': {'_index': index, '_id': digest}}) + '\n' +
            json.dumps(document, ensure_ascii=False, allow_nan=False) + '\n')


def request(base, path, method, body, content_type='application/json'):
    req = Request(base+path, data=body, method=method, headers={'Content-Type': content_type})
    with urlopen(req, timeout=60) as response:
        return json.load(response)


def check_bulk(response):
    failures = [item for item in response.get('items', [])
                if any(value.get('status', 500) >= 300 for value in item.values())]
    if response.get('errors') or failures:
        raise RuntimeError(f'Bulk indexing failed: {json.dumps(failures[:3])}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', type=Path)
    parser.add_argument('--url', default='http://127.0.0.1:9210')
    parser.add_argument('--index', default='packets-mbm-001')
    parser.add_argument('--capture-id', help='Default: SHA-256 of CSV bytes')
    parser.add_argument('--dry-run', type=Path, help='Write NDJSON without connecting')
    args = parser.parse_args()
    if args.dry_run and args.dry_run.resolve() == args.csv_file.resolve():
        parser.error('CSV input and NDJSON output must be different files')
    if not re.fullmatch(r'packets-mbm-[a-z0-9_-]+', args.index):
        parser.error('index must match packets-mbm-[a-z0-9_-]+')
    parsed = urlsplit(args.url)
    if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.path not in ('', '/'):
        parser.error('this unauthenticated importer only supports local HTTP endpoints')
    base = args.url.rstrip('/')
    capture = args.capture_id
    if not capture:
        with args.csv_file.open('rb') as source:
            capture = hashlib.file_digest(source, 'sha256').hexdigest()
    output = None
    if args.dry_run:
        args.dry_run.parent.mkdir(parents=True, exist_ok=True)
        output = args.dry_run.open('w', encoding='utf-8', newline='\n')
    else:
        request(base, '/_index_template/packets-mbm', 'PUT', json.dumps(template()).encode())
    try:
        batch = []
        count = 0
        with args.csv_file.open(encoding='utf-8-sig', newline='') as source:
            reader = csv.DictReader(source, delimiter=';')
            if not reader.fieldnames or 'frame.time_epoch' not in reader.fieldnames:
                raise ValueError('CSV header must include frame.time_epoch')
            for number, row in enumerate(reader, 1):
                try:
                    document = convert_row(row)
                except ValueError as error:
                    raise ValueError(f'CSV record {number}: {error}') from error
                batch.append(bulk_lines(document, args.index, capture, number))
                count += 1
                if len(batch) == 500:
                    flush(batch, base, output)
                    batch.clear()
            if batch:
                flush(batch, base, output)
        print(f'{count} records {"converted (dry run)" if output else "indexed"}')
    finally:
        if output:
            output.close()


def flush(batch, base, output):
    payload = ''.join(batch)
    if output:
        output.write(payload)
    else:
        check_bulk(request(base, '/_bulk?refresh=wait_for', 'POST', payload.encode(), 'application/x-ndjson'))


if __name__ == '__main__':
    main()
