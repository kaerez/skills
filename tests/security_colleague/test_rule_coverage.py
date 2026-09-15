"""Synthetic regression fixtures only. TLP:GREEN. (C) Erez Kalman.

Every host, rule and file here is invented, drawn only from .invalid names and
TEST-NET-3 addresses, and the suite performs no network or DNS access at all.
"""
import ast
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'plugins/security-colleague/skills/security-colleague/scripts'))
import rule_coverage as coverage

VIEW_HOSTS = ['watch.example.invalid', 'watch-cdn.example.invalid', 'assets.example.invalid']
AUTHOR_HOSTS = ['console.example.invalid', 'console.cluster-50.example.invalid',
                'studio.example.invalid', 'api.example.invalid']
TOP_LEVEL_KEYS = ['default_action', 'effective_decisions', 'fail_open', 'inert_rules',
                  'limitations', 'rules', 'schema_version', 'scope', 'shape', 'tool',
                  'totals', 'uncovered_evidence_hosts']


def report(hosts, rules, default_action='allow'):
    return coverage.build_report(hosts, rules, default_action)


def decisions_by_host(result):
    return {row['host']: row for row in result['effective_decisions']}


def run_cli(argv):
    """Drive main() with a patched argv and return whatever it wrote to stdout."""
    out, err = io.StringIO(), io.StringIO()
    saved = sys.argv
    sys.argv = ['rule_coverage.py'] + argv
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            coverage.main()
    finally:
        sys.argv = saved
    return out.getvalue()


def run_cli_expecting_error(case, argv):
    out, err = io.StringIO(), io.StringIO()
    saved = sys.argv
    sys.argv = ['rule_coverage.py'] + argv
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with case.assertRaises(SystemExit):
                coverage.main()
    finally:
        sys.argv = saved
    return err.getvalue()


class RuleCoverageTests(unittest.TestCase):
    def test_exact_fqdn_block_misses_the_cluster_direct_twin(self):
        """Regression: an exact-FQDN block does not cover the cluster-direct twin."""
        result = report(['console.example.invalid', 'console.cluster-50.example.invalid'],
                        ['block:fqdn:console.example.invalid'])
        self.assertEqual(result['uncovered_evidence_hosts'],
                         ['console.cluster-50.example.invalid'])
        rows = decisions_by_host(result)
        self.assertEqual(rows['console.example.invalid']['decision'], 'block')
        self.assertEqual(rows['console.cluster-50.example.invalid']['decision'], 'allow')

    def test_domain_rule_covers_the_domain_and_every_subdomain(self):
        """Regression: a domain rule was read as covering the bare name only."""
        result = report(['example.invalid', 'console.example.invalid',
                         'console.cluster-50.example.invalid', 'a.b.example.invalid'],
                        ['block:domain:example.invalid'])
        self.assertEqual(result['uncovered_evidence_hosts'], [])
        self.assertEqual(result['totals']['blocked'], 4)
        self.assertEqual(result['totals']['allowed'], 0)

    def test_domain_rule_does_not_match_a_lookalike_registrable_name(self):
        """Regression: a bare string suffix test blocks notexample.invalid too."""
        result = report(['notexample.invalid', 'console.notexample.invalid',
                         'console.example.invalid'],
                        ['block:domain:example.invalid'])
        self.assertEqual(result['uncovered_evidence_hosts'],
                         ['console.notexample.invalid', 'notexample.invalid'])
        self.assertFalse(coverage.rule_matches(coverage.parse_rule('block:domain:example.invalid'),
                                               'notexample.invalid'))

    def test_first_matching_rule_wins_so_an_allow_survives_a_later_domain_block(self):
        """Regression: precedence ignored, so the viewing host died with the authoring host."""
        result = report(['watch.example.invalid', 'console.example.invalid'],
                        ['allow:fqdn:watch.example.invalid', 'block:domain:example.invalid'])
        rows = decisions_by_host(result)
        self.assertEqual(rows['watch.example.invalid']['decision'], 'allow')
        self.assertEqual(rows['watch.example.invalid']['matched_index'], 0)
        self.assertEqual(rows['console.example.invalid']['decision'], 'block')
        self.assertEqual(rows['console.example.invalid']['matched_index'], 1)
        self.assertEqual(rows['console.example.invalid']['matched_rule'],
                         'block:domain:example.invalid')

    def test_hosts_no_rule_names_are_listed_as_uncovered(self):
        """Regression: a five-host list was presented as complete while three hosts matched nothing."""
        result = report(VIEW_HOSTS + AUTHOR_HOSTS,
                        ['block:fqdn:console.example.invalid',
                         'block:fqdn:studio.example.invalid'])
        self.assertEqual(result['uncovered_evidence_hosts'],
                         ['api.example.invalid', 'assets.example.invalid',
                          'console.cluster-50.example.invalid', 'watch-cdn.example.invalid',
                          'watch.example.invalid'])
        self.assertEqual(result['totals']['uncovered'], 5)

    def test_a_rule_matching_no_evidence_is_reported_as_inert(self):
        """Regression: filler entries padded a list to a number that felt complete."""
        result = report(['console.example.invalid'],
                        ['block:fqdn:console.example.invalid',
                         'block:fqdn:padding.example.invalid',
                         'block:domain:absent.invalid'])
        self.assertEqual(result['inert_rules'],
                         ['block:domain:absent.invalid', 'block:fqdn:padding.example.invalid'])
        self.assertEqual(result['totals']['inert'], 2)

    def test_shape_is_derived_for_blocklist_allowlist_combined_and_empty(self):
        """Regression: the failure mode was described without naming the rule set's shape."""
        cases = [
            ('blocklist', ['block:domain:example.invalid'], 'allow'),
            ('allowlist', ['allow:fqdn:watch.example.invalid'], 'block'),
            ('combined', ['allow:fqdn:watch.example.invalid', 'block:domain:example.invalid'],
             'block'),
            ('empty', [], 'allow'),
        ]
        for shape, rules, default_action in cases:
            with self.subTest(shape=shape):
                self.assertEqual(report(VIEW_HOSTS, rules, default_action)['shape'], shape)

    def test_default_allow_reports_an_unbounded_surface_without_a_count(self):
        """Regression: a fail-open blocklist was scored as if its residual surface were countable."""
        result = report(VIEW_HOSTS + AUTHOR_HOSTS, ['block:domain:example.invalid'], 'allow')
        self.assertTrue(result['fail_open']['unbounded'])
        explanation = result['fail_open']['explanation']
        self.assertIn('BY CONSTRUCTION', explanation)
        self.assertIn('cannot be enumerated', explanation)
        self.assertNotRegex(explanation, r'\d')

    def test_default_block_reports_a_bounded_and_listable_surface(self):
        """Regression: an allowlist was called fail-open like the blocklist it replaced."""
        result = report(VIEW_HOSTS + AUTHOR_HOSTS,
                        ['allow:fqdn:watch.example.invalid'], 'block')
        self.assertFalse(result['fail_open']['unbounded'])
        self.assertIn('finite', result['fail_open']['explanation'])
        self.assertEqual(result['totals']['allowed'], 1)
        self.assertEqual(result['totals']['blocked'], 6)
        self.assertEqual(len(result['uncovered_evidence_hosts']), 6)

    def test_evidence_loads_from_inventory_json(self):
        """Regression: an inventory report was retyped by hand into a rule review."""
        document = {'hosts': [{'host': 'watch.example.invalid', 'kind': 'hostname'},
                              {'host': 'console.example.invalid', 'kind': 'hostname'},
                              {'host': '203.0.113.7', 'kind': 'ip_literal'}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'inventory.json'
            path.write_text(json.dumps(document), encoding='utf-8')
            self.assertEqual(coverage.load_evidence(path, 1 << 20),
                             ['watch.example.invalid', 'console.example.invalid', '203.0.113.7'])

    def test_evidence_loads_from_a_newline_delimited_host_list(self):
        """Regression: a gateway log export could not be fed in without conversion."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'gateway.txt'
            path.write_text('# exported hosts\nWatch.Example.invalid.\n\n'
                            'console.example.invalid\n', encoding='utf-8')
            self.assertEqual(coverage.load_evidence(path, 1 << 20),
                             ['watch.example.invalid', 'console.example.invalid'])

    def test_ip_literals_are_counted_but_never_matched_by_name_rules(self):
        """Regression: an address in the evidence was reported as covered by a domain rule."""
        result = report(['console.example.invalid', '203.0.113.7', '203.0.113.8'],
                        ['block:domain:example.invalid'])
        self.assertEqual(result['totals']['ip_literals'], 2)
        self.assertEqual(result['totals']['evidence_hosts'], 1)
        self.assertNotIn('203.0.113.7', json.dumps(result['effective_decisions']))
        self.assertEqual(result['uncovered_evidence_hosts'], [])

    def test_malformed_rule_specifications_are_rejected(self):
        """Regression: an unparsed rule was silently treated as matching nothing."""
        for spec in ['block:example.invalid', 'deny:domain:example.invalid',
                     'block:regex:example.invalid', 'block:domain:', 'block:domain:invalid',
                     'block:fqdn:host name.invalid', 'block:fqdn:https://host.invalid',
                     'block:fqdn:203.0.113.7', 'block:domain:example.invalid:443']:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                coverage.parse_rule(spec)

    def test_malformed_evidence_is_rejected_rather_than_read_as_empty(self):
        """Regression: an unreadable evidence file scored as full coverage."""
        samples = ['', '{"hosts": "watch.example.invalid"}', '{"hosts": [{"host": 1}]}',
                   '{"hosts": [{"host": "watch.example.invalid", "kind": "ip_literal"}]}',
                   'https://watch.example.invalid/path']
        with tempfile.TemporaryDirectory() as directory:
            for index, text in enumerate(samples):
                path = Path(directory) / f'evidence-{index}.txt'
                path.write_text(text, encoding='utf-8')
                with self.subTest(text=text), self.assertRaises(ValueError):
                    coverage.load_evidence(path, 1 << 20)

    def test_output_never_overwrites_an_input_file(self):
        """Regression: a report written over its own evidence destroyed the evidence."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'gateway.txt'
            path.write_text('console.example.invalid\n', encoding='utf-8')
            message = run_cli_expecting_error(self, [
                '--evidence', str(path), '--rule', 'block:domain:example.invalid',
                '--output', str(path)])
            self.assertIn('must not overwrite', message)
            self.assertEqual(path.read_text(encoding='utf-8'), 'console.example.invalid\n')

    def test_totals_agree_with_the_lists_they_summarize(self):
        """Regression: counts were quoted that no list in the report supported."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'gateway.txt'
            path.write_text('\n'.join(VIEW_HOSTS + AUTHOR_HOSTS + ['203.0.113.7']) + '\n',
                            encoding='utf-8')
            result = json.loads(run_cli([
                '--evidence', str(path),
                '--rule', 'allow:fqdn:watch.example.invalid',
                '--rule', 'block:domain:example.invalid',
                '--rule', 'block:fqdn:padding.example.invalid']))
        totals = result['totals']
        self.assertEqual(totals['evidence_hosts'], len(result['effective_decisions']))
        self.assertEqual(totals['allowed'] + totals['blocked'], totals['evidence_hosts'])
        self.assertEqual(totals['uncovered'], len(result['uncovered_evidence_hosts']))
        self.assertEqual(totals['inert'], len(result['inert_rules']))
        self.assertEqual(totals['rules'], len(result['rules']))
        self.assertEqual(totals['ip_literals'], 1)
        self.assertEqual(result['inert_rules'], ['block:fqdn:padding.example.invalid'])

    def test_no_network_capable_module_is_imported(self):
        """Regression: a no-network claim was made in prose while the code could dial out."""
        tree = ast.parse(Path(coverage.__file__).read_text(encoding='utf-8'))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or '')
        for banned in ['socket', 'ssl', 'http', 'http.client', 'urllib.request',
                       'asyncio', 'ftplib', 'smtplib', 'subprocess']:
            self.assertNotIn(banned, imported)

    def test_report_carries_the_house_stamp_and_a_stable_key_set(self):
        """Regression: a report was quoted with no tool version and no stated scope."""
        result = report(VIEW_HOSTS, ['block:domain:example.invalid'])
        self.assertEqual(sorted(result), TOP_LEVEL_KEYS)
        self.assertEqual(result['schema_version'], 1)
        self.assertEqual(result['tool'], {'name': 'rule_coverage', 'version': coverage.VERSION})
        self.assertIn('no network', result['scope'])
        self.assertGreaterEqual(len(result['limitations']), 6)
        for sentence in result['limitations']:
            self.assertTrue(sentence[0].isupper(), sentence)
            self.assertTrue(sentence.endswith('.'), sentence)


if __name__ == '__main__':
    unittest.main()
