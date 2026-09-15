#!/usr/bin/env python3
"""Validate this repository's package links and synchronized metadata, offline.

TLP:GREEN. (C) Erez Kalman. This is not a complete vendor schema validator.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate():
    openai = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
    claude = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
    assert openai['name'] == claude['name']
    assert claude['owner']['name'] == 'Erez Kalman'
    assert len({p['name'] for p in openai['plugins']}) == len(openai['plugins'])
    ce = {p['name']: p for p in claude['plugins']}
    assert set(ce) == {p['name'] for p in openai['plugins']}
    for entry in openai['plugins']:
        name = entry['name']
        expected = './plugins/' + name
        assert entry['source'] == {'source': 'local', 'path': expected}
        assert ce[name]['source'] == expected
        assert entry['policy']['installation'] == 'AVAILABLE'
        assert entry['policy']['authentication'] == 'ON_INSTALL'
        assert entry['category']
        plugin = ROOT / expected
        om = json.loads((plugin / '.codex-plugin/plugin.json').read_text())
        cm = json.loads((plugin / '.claude-plugin/plugin.json').read_text())
        assert om['name'] == cm['name'] == name
        assert om['version'] == cm['version']
        assert re.fullmatch(r'\d+\.\d+\.\d+', om['version'])
        assert om['author']['name'] == cm['author']['name'] == 'Erez Kalman'
        assert om['repository'] == cm['repository'] == 'https://github.com/kaerez/skills'
        core = plugin / 'skills' / name
        body = (core / 'SKILL.md').read_text(encoding='utf-8')
        assert re.search(r'^name: ' + re.escape(name) + r'$', body, re.M)
        assert 'TLP:GREEN' in body and '(C) Erez Kalman' in body
        assert 'Package version: **' + om['version'] + '**' in body
        for doc in core.rglob('*.md'):
            text = doc.read_text(encoding='utf-8')
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target or target.startswith('#'):
                    continue
                destination = (doc.parent / target.split('#')[0]).resolve()
                assert destination.is_relative_to(core.resolve()), (doc.name, target)
                assert destination.exists(), (doc.name, target)
        for script in (core / 'scripts').glob('*.py'):
            compile(script.read_text(encoding='utf-8'), script.name, 'exec')
        for script in re.findall(r'`(scripts/[^`]+\.py)`', body):
            assert (core / script).is_file(), script
        documented = set(re.findall(r'`(scripts/[^`]+\.py)`', body))
        bundled = {'scripts/' + script.name for script in (core / 'scripts').glob('*.py')}
        assert bundled <= documented, ('undocumented scripts', sorted(bundled - documented))
        changelog = (plugin / 'CHANGELOG.md').read_text(encoding='utf-8')
        headings = re.findall(r'^## (\d+\.\d+\.\d+)', changelog, re.M)
        assert headings, 'CHANGELOG.md has no version heading'
        assert headings[0] == om['version'], ('changelog version', headings[0], om['version'])
        assert 'TLP:GREEN' in changelog and '(C) Erez Kalman' in changelog
    print('PASS: catalogs, package names/versions, changelog sync, markings, '
          'script documentation, relative references, and Python syntax')


if __name__ == '__main__':
    validate()
