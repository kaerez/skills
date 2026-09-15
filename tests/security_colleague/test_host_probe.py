"""Synthetic regression fixtures only. TLP:GREEN. (C) Erez Kalman.

Exercises the DNS wire codec against a local stub resolver on 127.0.0.1, so the
suite needs no outbound DNS and contacts no real name server.
"""
import socket
import struct
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'plugins/security-colleague/skills/security-colleague/scripts'))
import host_probe as probe


def encode(name):
    return probe.encode_name(name)


def answer_packet(qid, question, records, rcode=0, truncated=False):
    flags = 0x8180 | rcode | (0x0200 if truncated else 0)
    packet = struct.pack('!HHHHHH', qid, flags, 1, len(records), 0, 0)
    packet += encode(question) + struct.pack('!HH', 1, 1)
    for owner, rtype, value in records:
        packet += encode(owner)
        if rtype == 'CNAME':
            rdata = encode(value)
            packet += struct.pack('!HHIH', 5, 1, 60, len(rdata)) + rdata
        else:
            rdata = bytes(int(part) for part in value.split('.'))
            packet += struct.pack('!HHIH', 1, 1, 60, len(rdata)) + rdata
    return packet


class StubResolver:
    """Minimal UDP name server that answers from a fixed table."""

    def __init__(self, table):
        self.table = table
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 0))
        self.address = self.sock.getsockname()[0]
        self.port = self.sock.getsockname()[1]
        self.queries = []
        self.running = True
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        self.sock.settimeout(0.5)
        while self.running:
            try:
                data, peer = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            qid = struct.unpack('!H', data[:2])[0]
            try:
                name, _ = probe.decode_name(data, 12)
            except ValueError:
                continue
            self.queries.append(name.lower())
            records, rcode = self.table.get(name.lower(), ([], 3))
            try:
                self.sock.sendto(answer_packet(qid, name, records, rcode), peer)
            except OSError:
                return

    def stop(self):
        self.running = False
        self.sock.close()


TABLE = {
    'app.synthetic.invalid': ([('app.synthetic.invalid', 'CNAME', 'd1abc.cloudfront.net'),
                               ('d1abc.cloudfront.net', 'A', '203.0.113.10')], 0),
    'api.synthetic.invalid': ([('api.synthetic.invalid', 'CNAME',
                                'lb-1.eu-west-1.elb.amazonaws.com'),
                               ('lb-1.eu-west-1.elb.amazonaws.com', 'A', '203.0.113.11')], 0),
    'plain.synthetic.invalid': ([('plain.synthetic.invalid', 'A', '203.0.113.12')], 0),
}


class ForgingResolver:
    """Receives on one port and replies from another, as an off-path forger does."""

    def __init__(self, table):
        self.table = table
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 0))
        self.spoof = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.spoof.bind(('127.0.0.1', 0))
        self.address, self.port = self.sock.getsockname()
        self.running = True
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        self.sock.settimeout(0.5)
        while self.running:
            try:
                data, peer = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            qid = struct.unpack('!H', data[:2])[0]
            try:
                name, _ = probe.decode_name(data, 12)
            except ValueError:
                continue
            records, rcode = self.table.get(name.lower(), ([], 3))
            try:
                self.spoof.sendto(answer_packet(qid, name, records, rcode), peer)
            except OSError:
                return

    def stop(self):
        self.running = False
        self.sock.close()
        self.spoof.close()


class HostProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stub = StubResolver(TABLE)

    @classmethod
    def tearDownClass(cls):
        cls.stub.stop()

    def resolve(self, name):
        return probe.resolve_with(self.stub.address, name, timeout=2.0,
                                  port=self.stub.port)

    def test_wire_codec_round_trip_and_cname_chain(self):
        result = self.resolve('app.synthetic.invalid')
        self.assertTrue(result['exists'])
        self.assertEqual(result['chain'], ['d1abc.cloudfront.net'])
        self.assertEqual(result['addresses'], ['203.0.113.10'])
        self.assertEqual(result['errors'], [])

    def test_provider_classification_from_alias_suffix(self):
        self.assertEqual(probe.classify('d1abc.cloudfront.net'), 'AWS CloudFront')
        self.assertEqual(probe.classify('lb-1.eu-west-1.elb.amazonaws.com'),
                         'AWS Elastic Load Balancing (eu-west-1)')
        self.assertEqual(probe.classify('x.cdn.cloudflare.net'), 'Cloudflare')
        self.assertEqual(probe.classify('host.example.invalid'), 'unclassified')

    def test_allowed_and_blocked_hosts_can_share_a_provider(self):
        """The observation that defeats address-based and alias-based rules."""
        one = probe.classify(self.resolve('app.synthetic.invalid')['chain'][-1])
        two = probe.classify('d2xyz.cloudfront.net')
        self.assertEqual(one, two)

    def test_nxdomain_is_reported_without_an_address(self):
        result = self.resolve('absent.synthetic.invalid')
        self.assertFalse(result['exists'])
        self.assertEqual(result['rcode'], 'NXDOMAIN')
        self.assertEqual(result['addresses'], [])

    def test_host_without_cname_has_empty_chain(self):
        result = self.resolve('plain.synthetic.invalid')
        self.assertTrue(result['exists'])
        self.assertEqual(result['chain'], [])

    def test_variant_generation_covers_region_and_cluster_siblings(self):
        generated = probe.variants('backend.public-pr50.synthetic.invalid', ['eu'], 1)
        self.assertIn('backend.eu.public-pr50.synthetic.invalid', generated)
        self.assertIn('backend.public-pr49.synthetic.invalid', generated)
        self.assertIn('backend.public-pr51.synthetic.invalid', generated)
        self.assertIn('backend.public-preu-50.synthetic.invalid', generated)
        self.assertIn('backend.public-pr50.synthetic.invalid', generated)
        for name in generated:
            self.assertRegex(name, probe.HOSTNAME)

    def test_variant_generation_is_stable_for_a_plain_host(self):
        generated = probe.variants('sdk.synthetic.invalid', ['eu'], 1)
        self.assertIn('sdk.synthetic.invalid', generated)
        self.assertIn('sdk.eu.synthetic.invalid', generated)

    def test_dry_run_performs_no_lookup(self):
        before = len(self.stub.queries)
        probe.variants('api.synthetic.invalid', ['eu'], 1)
        self.assertEqual(len(self.stub.queries), before)

    def test_named_resolvers_include_google_and_cloudflare(self):
        self.assertIn('8.8.8.8', probe.NAMED_RESOLVERS['google'])
        self.assertIn('1.1.1.1', probe.NAMED_RESOLVERS['cloudflare'])
        self.assertIn('9.9.9.9', probe.NAMED_RESOLVERS['quad9'])
        self.assertEqual(probe.NAMED_RESOLVERS['system'], [])

    def test_inventory_hostnames_are_reused_and_ip_literals_skipped(self):
        import json
        import tempfile
        document = {'hosts': [{'host': 'api.synthetic.invalid', 'kind': 'hostname'},
                              {'host': '203.0.113.5', 'kind': 'ip_literal'}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'inv.json'
            path.write_text(json.dumps(document), encoding='utf-8')
            self.assertEqual(probe.hosts_from_inventory(path), ['api.synthetic.invalid'])

    def test_compression_pointer_loop_is_rejected(self):
        looping = struct.pack('!HHHHHH', 1, 0x8180, 0, 0, 0, 0) + b'\xc0\x0c'
        with self.assertRaises(ValueError):
            probe.decode_name(looping, 12)

    def test_transaction_id_mismatch_is_rejected(self):
        packet = answer_packet(999, 'plain.synthetic.invalid',
                               [('plain.synthetic.invalid', 'A', '203.0.113.12')])
        with self.assertRaises(ValueError):
            probe.parse_response(packet, 1)

    def test_truncated_response_is_rejected_not_guessed(self):
        with self.assertRaises(ValueError):
            probe.parse_response(b'\x00\x01', 1)

    def test_reply_from_another_source_address_is_discarded(self):
        """The socket is connected, so the kernel drops off-path datagrams."""
        forger = ForgingResolver(TABLE)
        try:
            answer = probe.ask(forger.address, 'plain.synthetic.invalid', 'A',
                               timeout=0.4, retries=1, port=forger.port)
        finally:
            forger.stop()
        self.assertIn('error', answer)
        self.assertNotIn('answers', answer)

    def test_response_bit_must_be_set(self):
        """A query replayed back at the client is not an answer."""
        packet = answer_packet(7, 'plain.synthetic.invalid',
                               [('plain.synthetic.invalid', 'A', '203.0.113.12')])
        query_flags = struct.pack('!H', 0x0100)
        forged = packet[:2] + query_flags + packet[4:]
        with self.assertRaises(ValueError):
            probe.parse_response(forged, 7)

    def test_question_section_must_echo_the_query(self):
        """An answer for a name we never asked about is not ours."""
        packet = answer_packet(7, 'other.synthetic.invalid',
                               [('other.synthetic.invalid', 'A', '203.0.113.99')])
        self.assertEqual(probe.parse_response(packet, 7)['rcode'], 0)
        with self.assertRaises(ValueError):
            probe.parse_response(packet, 7, 'plain.synthetic.invalid')


if __name__ == '__main__':
    unittest.main()
