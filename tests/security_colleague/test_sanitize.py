"""Synthetic regression fixtures only. TLP:GREEN. (C) Erez Kalman.

Every identifier here is invented. No real capture, host, tenant or token.
"""
import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'plugins/security-colleague/skills/security-colleague/scripts'))
import har_inventory as inventory
import har_sanitize as sanitize

SYNTHETIC_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
SYNTHETIC_TOKEN = 'QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ'


def entry(method, url, status=200, post=None, mime='application/json',
          req_headers=(), resp_headers=(), body=None, ws=None):
    record = {
        'startedDateTime': '2026-01-01T00:00:00.000Z', 'time': 12,
        'request': {'method': method, 'url': url, 'httpVersion': 'HTTP/2',
                    'cookies': [{'name': 'sid', 'value': SYNTHETIC_TOKEN}],
                    'headers': [{'name': name, 'value': value} for name, value in req_headers],
                    'queryString': [], 'headersSize': -1, 'bodySize': -1},
        'response': {'status': status, 'statusText': 'OK', 'httpVersion': 'HTTP/2',
                     'cookies': [], 'content': {'size': 10, 'mimeType': mime,
                                                'text': body or ''},
                     'headers': [{'name': name, 'value': value} for name, value in resp_headers],
                     'redirectURL': '', 'headersSize': -1, 'bodySize': -1},
        'cache': {}, 'timings': {'send': 1, 'wait': 2, 'receive': 3},
    }
    if post:
        record['request']['postData'] = {'mimeType': 'application/json', 'text': post}
    if ws:
        record['_webSocketMessages'] = ws
    return record


def capture():
    """Shared host carrying an allowed registration and a prohibited mutation."""
    return {'log': {'version': '1.2', 'creator': {'name': 'synthetic', 'version': '0'},
                    '_exporterExtension': SYNTHETIC_TOKEN,
                    'entries': [
        entry('GET', 'https://view.synthetic.invalid/on-demand/' + SYNTHETIC_UUID,
              mime='text/html'),
        entry('POST', 'https://api.synthetic.invalid/v1/registrations',
              post='{"email":"person@example.invalid","name":"Synthetic Person",'
                   '"national_id":"123456789"}',
              req_headers=[('Authorization', 'Bearer ' + SYNTHETIC_TOKEN)]),
        entry('POST', 'https://api.synthetic.invalid/graphql',
              post='{"operationName":"EventQuery","query":"query EventQuery { event { id } }"}'),
        entry('POST', 'https://api.synthetic.invalid/graphql',
              post='{"operationName":"CreateEvent",'
                   '"query":"mutation CreateEvent { createEvent { id } }"}'),
        # Percent-encoded separators: the defect that leaked a real identifier.
        entry('GET', 'https://assets.synthetic.invalid/event%2F' + SYNTHETIC_UUID
                     + '%2Fresources%2FLogo.png', mime='image/png'),
        entry('GET', 'https://api.synthetic.invalid/magic?token=' + SYNTHETIC_TOKEN
                     + '&utm_source=email&mkt_tok=' + SYNTHETIC_TOKEN),
        entry('GET', 'wss://socket.synthetic.invalid/live',
              ws=[{'type': 'send', 'data': 'chat:' + SYNTHETIC_TOKEN}]),
    ]}}


def write(directory, name, document):
    path = Path(directory) / name
    path.write_text(json.dumps(document), encoding='utf-8')
    return path


class SanitizeTests(unittest.TestCase):
    def test_percent_encoded_identifier_is_redacted(self):
        """Regression: encoded separators must not hide a path segment."""
        result, _ = sanitize.sanitize_document(capture())
        serialized = json.dumps(result)
        self.assertNotIn(SYNTHETIC_UUID, serialized)
        self.assertNotIn('%2F' + SYNTHETIC_UUID, serialized)
        shapes = [item['_security_colleague']['path_shape'] for item in result['log']['entries']]
        self.assertIn('/event/{uuid-1}/resources/Logo.png', shapes)

    def test_residual_scan_is_independent_of_the_redaction_rules(self):
        """Regression: a scan reusing the redactor's pattern reports false clean."""
        leaky = {'log': {'entries': [{
            'request': {'method': 'GET',
                        'url': 'https://host.invalid/x',
                        'httpVersion': 'HTTP/2'},
            'response': {'status': 200}}]}}
        result, _ = sanitize.sanitize_document(leaky)
        planted = json.dumps(result).replace('"/x"', '"/event%2F' + SYNTHETIC_UUID + '"')
        findings = sanitize.residual_findings(planted)
        self.assertTrue(any(item['pattern'] == 'uuid' for item in findings), findings)
        self.assertTrue(any(item['form'] == 'percent_decoded' for item in findings), findings)

    def test_clean_output_reports_no_residual_findings(self):
        result, _ = sanitize.sanitize_document(capture())
        self.assertEqual(sanitize.residual_findings(json.dumps(result, indent=2)), [])

    def test_shared_host_read_and_write_are_distinguishable(self):
        result, _ = sanitize.sanitize_document(capture())
        rows = [(item['request']['url'], item['_security_colleague']['operation']['name'])
                for item in result['log']['entries']]
        names = {name for _, name in rows if name}
        self.assertEqual(names, {'EventQuery', 'CreateEvent'})
        paths = {url.rsplit('/', 1)[-1] for url, _ in rows}
        self.assertIn('registrations', paths)
        self.assertIn('graphql', paths)

    def test_secrets_bodies_and_headers_are_not_retained(self):
        source = capture()
        before = copy.deepcopy(source)
        result, _ = sanitize.sanitize_document(source)
        serialized = json.dumps(result, ensure_ascii=False)
        for secret in [SYNTHETIC_TOKEN, 'person@example.invalid', 'Synthetic Person',
                       '123456789', 'chat:', 'Bearer']:
            self.assertNotIn(secret, serialized)
        self.assertEqual(source, before)
        annotation = result['log']['entries'][1]['_security_colleague']
        self.assertIn('authorization', annotation['request_headers_present'])
        self.assertTrue(annotation['request_body_present'])

    def test_tracking_keys_dropped_and_other_values_placeheld(self):
        result, _ = sanitize.sanitize_document(capture())
        note = result['log']['_security_colleague']
        self.assertEqual(note['dropped_tracking_query_keys'],
                         {'mkt_tok': 1, 'utm_source': 1})
        magic = [item for item in result['log']['entries']
                 if item['_security_colleague']['path_shape'] == '/magic'][0]
        self.assertEqual(magic['request']['queryString'], [{'name': 'token', 'value': '{value}'}])

    def test_placeholders_are_consistent_and_mapping_is_separate(self):
        source = capture()
        source['log']['entries'].append(copy.deepcopy(source['log']['entries'][0]))
        result, marks = sanitize.sanitize_document(source)
        first = result['log']['entries'][0]['request']['url']
        last = result['log']['entries'][-1]['request']['url']
        self.assertEqual(first, last)
        self.assertIn('{uuid-1}', first)
        self.assertNotIn(SYNTHETIC_UUID, json.dumps(result))
        self.assertIn(SYNTHETIC_UUID, json.dumps(marks.mapping()))
        self.assertEqual(result['log']['_security_colleague']['placeholder_mapping_location'],
                         'separate --mapping file, or discarded')

    def test_retain_hosts_keeps_real_hostnames_only_when_requested(self):
        default, _ = sanitize.sanitize_document(capture())
        self.assertNotIn('api.synthetic.invalid', json.dumps(default))
        retained, _ = sanitize.sanitize_document(capture(), retain_hosts=True)
        self.assertIn('api.synthetic.invalid', json.dumps(retained))

    def test_websocket_presence_recorded_without_message_content(self):
        result, _ = sanitize.sanitize_document(capture())
        flags = [item['_security_colleague']['websocket_messages_present']
                 for item in result['log']['entries']]
        self.assertTrue(any(flags))
        # The key name is recorded as parse coverage; no message content survives.
        self.assertNotIn('_webSocketMessages', json.dumps(result['log']['entries']))
        self.assertNotIn('chat:', json.dumps(result))
        self.assertIn('_webSocketMessages',
                      result['log']['_security_colleague']['source_structure']['exporter_extensions'])

    def test_multipart_and_unparsable_bodies_are_reported_not_inspected(self):
        source = capture()
        source['log']['entries'].append(entry(
            'POST', 'https://api.synthetic.invalid/upload',
            post='--b\r\nContent-Disposition: form-data; name="f"\r\n\r\n' + SYNTHETIC_TOKEN))
        result, _ = sanitize.sanitize_document(source)
        last = result['log']['entries'][-1]['_security_colleague']
        self.assertTrue(last['request_body_present'])
        self.assertIsNone(last['operation']['name'])
        self.assertNotIn(SYNTHETIC_TOKEN, json.dumps(result))

    def test_malformed_input_rejected(self):
        for bad in [[], {}, {'log': {}}, {'log': {'entries': [None]}},
                    {'log': {'entries': [{'request': {}}]}}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                sanitize.sanitize_document(bad)

    def test_unsupported_url_counted_not_passed_through(self):
        source = {'log': {'entries': [{
            'request': {'method': 'GET', 'url': 'javascript:alert(' + SYNTHETIC_TOKEN + ')'},
            'response': {'status': 200}}]}}
        result, _ = sanitize.sanitize_document(source)
        self.assertEqual(result['log']['_security_colleague']['skipped'],
                         {'unsupported_url': 1})
        self.assertNotIn(SYNTHETIC_TOKEN, json.dumps(result))

    def test_validate_only_reports_coverage(self):
        report = sanitize.validate_structure(capture())
        self.assertTrue(report['has_log_entries'])
        self.assertEqual(report['entries'], 7)
        self.assertEqual(report['websocket_entries'], 1)
        self.assertEqual(report['entries_with_request_body'], 3)
        self.assertIn('_exporterExtension', report['exporter_extensions'])
        self.assertIn('_webSocketMessages', report['exporter_extensions'])

    def test_validate_only_handles_non_har_json(self):
        report = sanitize.validate_structure({'not': 'a har'})
        self.assertFalse(report['has_log_entries'])
        self.assertEqual(report['entries'], 0)

    def test_output_file_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'out.har'
            path.write_text('keep', encoding='utf-8')
            result, _ = sanitize.sanitize_document(capture())
            with self.assertRaises(ValueError):
                sanitize.write_new(path, result)
            self.assertEqual(path.read_text(encoding='utf-8'), 'keep')

    def test_inventory_totals_replace_hand_counting(self):
        """Regression: a review quoted 17 hosts when the inventory held 16."""
        with tempfile.TemporaryDirectory() as directory:
            path = write(directory, 'synthetic.har', capture())
            report = inventory.summarize([('view', path), ('create', path)])
            self.assertEqual(report['schema_version'], 2)
            self.assertEqual(report['totals']['host_count'], len(report['hosts']))
            self.assertEqual(report['totals']['host_count'], 4)
            self.assertEqual(report['totals']['shared_across_workflows_count'], 4)
            self.assertNotIn(SYNTHETIC_TOKEN, json.dumps(report))

    def test_no_placeholder_text_is_mistaken_for_a_residual(self):
        self.assertEqual(sanitize.residual_findings(
            '{"url":"https://host-1.invalid/event/{uuid-1}/{token-2}"}'), [])
        self.assertTrue(re.search(r'\{uuid-1\}', '{uuid-1}'))


if __name__ == '__main__':
    unittest.main()
