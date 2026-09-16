#!/usr/bin/env python3
"""Validate this repository's package links and synchronized metadata, offline.

TLP:GREEN. (C) Erez Kalman. This is not a complete vendor schema validator.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG_FILES = {
    'Report format': 'references/report-format.md',
    'Consumption review': 'references/consumption-review.md',
    'Enforcement': 'references/enforcement.md',
    'Evidence': 'references/evidence.md',
    'Sanitization': 'references/sanitization.md',
    'Web investigation': 'references/web-investigation.md',
    'SKILL.md': 'SKILL.md',
}


def _columns(row):
    """Count the `|`-delimited columns of one table row.

    Backtick spans are removed before splitting, so a pipe inside an inline code
    span such as `a|b` is cell text rather than a column delimiter.
    """
    cells = re.sub(r'\\\|', '', re.sub(r'`[^`]*`', '', row.strip()))
    if cells.startswith('|'):
        cells = cells[1:]
    if cells.endswith('|'):
        cells = cells[:-1]
    return len(cells.split('|'))


def _check_tables(doc, text):
    """Assert each table is a header row, a separator row, then data rows only."""
    lines = text.split('\n')
    fence = None
    for index, line in enumerate(lines):
        marker = re.match(r'\s*(`{3,}|~{3,})', line)
        if marker:
            opener = marker.group(1)
            if fence is None:
                fence = opener[0]
            elif opener[0] == fence:
                fence = None
            continue
        # Only column-0 tables are validated. An indented table is skipped rather
        # than failed, so a table nested in a list item cannot block a release.
        if fence or not re.fullmatch(r'\|(?:\s*:?-{3,}:?\s*\|)+', line):
            continue
        header = lines[index - 1] if index else ''
        assert header.startswith('|'), ('separator row without a header row', doc.name, index + 1)
        after = lines[index + 1] if index + 1 < len(lines) else ''
        assert after.startswith('|') or not after.strip(), (
            'prose between a table separator row and its first data row', doc.name, index + 2, after)
        width = _columns(header)
        assert _columns(line) == width, (
            'separator row column count', doc.name, index + 1, _columns(line), width)
        for offset, row in enumerate(lines[index + 1:]):
            if not row.startswith('|'):
                break
            assert _columns(row) == width, (
                'table row column count', doc.name, index + 2 + offset, _columns(row), width)


def _anchors(text):
    """Heading anchors the GitHub way: lowercase, keep alphanumeric/space/hyphen/underscore.

    Fenced blocks are removed first so a `#` comment inside an example is not
    harvested as a heading, which would let a broken fragment link pass.
    """
    bare = re.sub(r'^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*$', '', text, flags=re.M | re.S)
    return {re.sub(r'[^a-z0-9 _-]', '', heading.lower()).replace(' ', '-')
            for heading in re.findall(r'^#+ +(.+?)\s*$', bare, re.M)}


def _description(body):
    """The `description:` folded scalar from a SKILL.md YAML frontmatter block."""
    front = re.match(r'---\n(.*?)\n---\n', body, re.S)
    assert front, 'SKILL.md has no YAML frontmatter'
    block = re.search(r'^description: >-\n((?:[ \t]+\S.*(?:\n|\Z))+)', front.group(1), re.M)
    assert block, 'SKILL.md frontmatter has no folded description block'
    return ' '.join(block.group(1).split())


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
        described = _description(body)
        assert len(described) <= 1024, ('frontmatter description too long', name, len(described))
        for doc in core.rglob('*.md'):
            text = doc.read_text(encoding='utf-8')
            _check_tables(doc, text)
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target:
                    continue
                path, _, fragment = target.partition('#')
                destination = (doc.parent / path).resolve() if path else doc.resolve()
                assert destination.is_relative_to(core.resolve()), (doc.name, target)
                assert destination.exists(), (doc.name, target)
                if fragment and destination.suffix == '.md':
                    anchors = _anchors(destination.read_text(encoding='utf-8'))
                    assert fragment.lower() in anchors, (
                        'link fragment names no heading', doc.name, target, sorted(anchors))
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
        # Only the entry for the version being released is checked. Older entries
        # describe the tree as it was, so a later rename must not fail them.
        current = re.search(r'^## ' + re.escape(om['version']) + r'\b.*?(?=^## |\Z)',
                            changelog, re.M | re.S)
        assert current, ('changelog has no entry for this version', om['version'])
        for bullet in re.findall(r'^- [^\n]*(?:\n[ \t]+\S[^\n]*)*', current.group(0), re.M):
            text = ' '.join(bullet[2:].split())
            # A bullet names its file either as a "Human name:" prefix or as a
            # backticked path anywhere in the bullet.
            named = [CHANGELOG_FILES[key] for key in (text.partition(':')[0],) if key in CHANGELOG_FILES]
            named += [path for path in re.findall(r'`(references/[^`]+\.md|SKILL\.md)`', text)]
            # Only a bold span explicitly called a section is a claim about a
            # heading; bare bold is ordinary emphasis and is not asserted on.
            claims = re.findall(r'\*\*([^*]+)\*\* section|section \*\*([^*]+)\*\*', text)
            sections = [a or b for a, b in claims]
            for relative in dict.fromkeys(named):
                document = core / relative
                assert document.is_file(), ('changelog names a missing file', relative)
                content = document.read_text(encoding='utf-8')
                for section in sections:
                    assert re.search(r'^#+ .*' + re.escape(section), content, re.M | re.I), (
                        'changelog claims a section the file lacks', relative, section)
    print('PASS: catalogs, package names/versions, changelog sync, markings, '
          'script documentation, relative references, link fragments, table '
          'shape, changelog sections, description length, and Python syntax')


if __name__ == '__main__':
    validate()
