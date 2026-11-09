"""Launch the built .NET demo, verify HTTP behavior, always stop only our child."""
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT/'portfolio/access-control-demo'


class Client:
    def __init__(self, base):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.token = None

    def call(self,path,method='GET',body=None,csrf=True):
        headers = {'Content-Type':'application/json'}
        if csrf and self.token:
            headers['X-CSRF-TOKEN'] = self.token
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base+path,data=data,method=method,headers=headers)
        try:
            response = self.opener.open(request,timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else None

    def refresh_csrf(self):
        status, body = self.call('/api/csrf')
        assert status == 200
        self.token = body['token']

    def login(self,name,password):
        self.refresh_csrf()
        result = self.call('/api/login','POST',{'username':name,'password':password})
        if result[0] == 200:
            self.refresh_csrf()
        return result


def main():
    dll = PROJECT/'bin/Debug/net10.0/AccessControlDemo.dll'
    if not dll.exists():
        raise SystemExit('Build the project first: dotnet build portfolio/access-control-demo')
    # Choose an available local port; avoid assuming the user's 5087 is unused.
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0))
        port = probe.getsockname()[1]
    env = os.environ.copy()
    admin_password, reader_password = secrets.token_urlsafe(24),secrets.token_urlsafe(24)
    env.update(ASPNETCORE_ENVIRONMENT='Development',DEMO_ADMIN_USER='admin',
               DEMO_ADMIN_PASSWORD=admin_password,DEMO_READER_USER='reader',DEMO_READER_PASSWORD=reader_password)
    log_dir = ROOT/'review-work'
    log_dir.mkdir(exist_ok=True)
    with (log_dir/'access-control.log').open('w',encoding='utf-8') as log:
        process = subprocess.Popen(['dotnet',str(dll),'--contentRoot',str(PROJECT),
                                    '--urls',f'http://127.0.0.1:{port}'],
                                   cwd=PROJECT,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            base = f'http://127.0.0.1:{port}'
            anonymous=Client(base)
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('App exited; see review-work/access-control.log')
                try:
                    if anonymous.call('/api/csrf')[0] == 200:
                        break
                except (OSError,urllib.error.URLError):
                    time.sleep(.1)
            else:
                raise RuntimeError('App did not become ready')
            assert anonymous.call('/api/users')[0] == 401
            assert anonymous.call('/login/admin')[0] == 404
            assert anonymous.login('admin','incorrect-password')[0] == 401

            reader=Client(base)
            assert reader.login('reader',reader_password)[0] == 200
            assert reader.call('/api/users')[0] == 200
            assert reader.call('/api/users','POST',{'name':'Denied','age':22})[0] == 403

            admin=Client(base)
            assert admin.login('admin',admin_password)[0] == 200
            assert admin.call('/api/users','POST',{'name':'No CSRF','age':22},csrf=False)[0] == 400
            assert admin.call('/api/users','POST',{'name':'','age':200})[0] == 400
            code,created = admin.call('/api/users','POST',{'name':'<script>literal</script>','age':23})
            assert code == 201
            item_id = created['id']
            assert admin.call(f'/api/users/{item_id}','PUT',{'name':'Updated','age':24})[0] == 200
            assert admin.call(f'/api/users/{item_id}')[1]['name'] == 'Updated'
            assert admin.call(f'/api/users/{item_id}','DELETE')[0] == 204
            assert admin.call(f'/api/users/{item_id}')[0] == 404
            cookies = [c for c in admin.jar if c.name == 'portfolio.session']
            assert len(cookies)==1
            flags={key.lower():value for key,value in cookies[0]._rest.items()}
            assert 'httponly' in flags
            assert flags['samesite'].lower() == 'strict'
            assert admin.call('/api/logout','POST')[0] == 204
            assert admin.call('/api/users')[0] == 401

            # The limiter must eventually reject repeated failures; use a fresh anonymous client.
            brute=Client(base)
            statuses=[brute.login('admin','invalid-password')[0] for _ in range(6)]
            assert 429 in statuses
            print('PASS: anonymous/invalid login, role isolation, CSRF, input validation, CRUD, cookie flags, logout, rate limiting')
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == '__main__':
    main()
