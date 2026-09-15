"""Synthetic regression fixtures only. TLP:GREEN. (C) Erez Kalman."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'plugins/security-colleague/skills/security-colleague/scripts'))
import har_inventory as inventory
import har_minimize as minimize


def capture():
    return {'log': {'entries': [{
        'request': {'url': 'https://user:password@tenant.example/view?token=SECRET#private',
                    'method': 'POST', 'httpVersion': 'HTTP/2',
                    'headers': [{'name': 'Authorization', 'value': 'SECRET'}],
                    'postData': {'text': 'בדיקה Тест Synthetic Person test@example.invalid 123-45-6789'}},
        'response': {'status': 200, 'httpVersion': 'HTTP/2',
                     'content': {'text': 'SECRET medical details'}, 'cookies': [{'value': 'SECRET'}]},
        '_extension': {'secret': 'SECRET'}}], '_metadata': 'SECRET'}}


class HarTests(unittest.TestCase):
    def test_removes_sensitive_fields_without_modifying_original(self):
        source = capture()
        before = copy.deepcopy(source)
        result = minimize.minimize_document(source)
        serialized = json.dumps(result, ensure_ascii=False)
        for secret in ['SECRET', 'password', 'tenant.example', 'בדיקה', 'Тест', 'test@example.invalid', '123-45-6789', 'medical details']:
            self.assertNotIn(secret, serialized)
        self.assertEqual(source, before)
        self.assertEqual(result['log']['entries'][0]['request']['method'], 'POST')

    def test_consistent_host_placeholders(self):
        source = capture()
        source['log']['entries'].append(copy.deepcopy(source['log']['entries'][0]))
        entries = minimize.minimize_document(source)['log']['entries']
        self.assertEqual(entries[0]['request']['url'], entries[1]['request']['url'])
        self.assertIn('host-1.invalid', entries[0]['request']['url'])

    def test_explicit_host_retention_still_removes_url_secrets(self):
        result = minimize.minimize_document(capture(), retain_hosts=True)
        self.assertEqual(result['log']['entries'][0]['request']['url'], 'https://tenant.example/redacted')

    def test_malformed_entries_rejected(self):
        for bad in [[], {}, {'log': {'entries': [None]}}, {'log': {'entries': [{}]}}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                minimize.minimize_document(bad)

    def test_ambiguous_and_oversized_json_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'synthetic.json'
            for data in [b'{"x":1,"x":2}', b'{"x":NaN}', b'{', b'\xff']:
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    minimize.load_document(path, 1024)
            path.write_bytes(b'{}')
            with self.assertRaises(ValueError):
                minimize.load_document(path, 1)

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'output.har'
            path.write_text('keep')
            with self.assertRaises(ValueError):
                minimize.write_new(path, capture())
            self.assertEqual(path.read_text(), 'keep')

    def test_shared_post_host_remains_visible_without_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'synthetic.har'
            path.write_text(json.dumps(capture()))
            result = inventory.summarize([('view', path), ('create', path)])
            self.assertEqual(len(result['hosts']), 1)
            self.assertEqual(set(result['hosts'][0]['by_workflow']), {'view', 'create'})
            self.assertNotIn('SECRET', json.dumps(result))
            self.assertEqual(result['hosts'][0]['by_workflow']['view']['methods']['POST'], 1)

    def test_redirect_reference_is_not_a_captured_request(self):
        source = capture()
        source['log']['entries'][0]['response'].update(status=302, redirectURL='https://other.example/view')
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'synthetic.har'
            path.write_text(json.dumps(source))
            result = inventory.summarize([('view', path)])
            target = next(row for row in result['hosts'] if row['host'] == 'other.example')
            self.assertEqual(target['captured_requests'], 0)
            self.assertEqual(target['redirect_references_by_workflow']['view'], 1)


if __name__ == '__main__':
    unittest.main()
