"""Reconstructed partial workflow from storage lab 7 / image24.jpg.

Creates a dedicated demo bucket and object; downloads without overwriting files.
"""
import argparse
import hashlib
import io
import os
from pathlib import Path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',type=Path,default=Path('output/downloaded-demo.txt'))
    args = parser.parse_args()
    if args.download.exists():
        parser.error('output already exists; choose another path')
    from minio import Minio
    client = Minio('127.0.0.1:9010',access_key='portfolio_admin',
                   secret_key=os.environ['MINIO_PASSWORD'],secure=False)
    bucket='portfolio-demo-files'
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    content=b'University storage lab: reconstructed object-storage example.\n'
    name=hashlib.sha256(content).hexdigest()+'.txt'
    client.put_object(bucket,name,io.BytesIO(content),len(content),content_type='text/plain')
    response=client.get_object(bucket,name)
    try:
        actual=response.read()
    finally:
        response.close()
        response.release_conn()
    if hashlib.sha256(actual).digest()!=hashlib.sha256(content).digest():
        raise RuntimeError('Downloaded content hash mismatch')
    args.download.parent.mkdir(parents=True,exist_ok=True)
    with args.download.open('xb') as output:
        output.write(actual)
    print(f'Uploaded and verified: {bucket}/{name}')
