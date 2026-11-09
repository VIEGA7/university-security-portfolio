"""Build TShark command from storage lab 5; read an existing PCAP only."""
import argparse
from pathlib import Path
import subprocess

FIELDS = ['frame.time_epoch', 'frame.number', 'ip.src', 'ip.dst', 'frame.protocols',
          'http.host', 'tcp.srcport', 'tcp.dstport', 'udp.srcport', 'udp.dstport',
          'tls.handshake.extensions_server_name', 'frame.len', 'dns.qry.name',
          'http.request.method', 'http.response.code', 'tcp.flags', 'eth.src']


def command(pcap):
    args = ['tshark', '-r', str(pcap), '-Y', 'ip && (tcp || udp || icmp)', '-T', 'fields']
    for field in FIELDS:
        args.extend(['-e', field])
    return args + ['-E', 'header=y', '-E', 'separator=;', '-E', 'aggregator=,', '-E', 'quote=d']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcap', type=Path)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--show-command', action='store_true')
    args = parser.parse_args()
    if args.show_command:
        print(subprocess.list2cmdline(command(args.pcap)))
    else:
        if not args.pcap.is_file():
            parser.error('input PCAP does not exist')
        if args.pcap.resolve() == args.csv.resolve():
            parser.error('input and output must be different files')
        with args.csv.open('xb') as output:
            subprocess.run(command(args.pcap), stdout=output, check=True)
