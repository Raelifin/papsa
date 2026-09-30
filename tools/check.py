#!/usr/bin/env python3
"""Validate index.html by loading it in headless Chrome and reading the page's own #report.

Usage: python3 tools/check.py [path/to/index.html]

Exits 1 if the report lists spec errors, duplicate table keys, or unparseable snippets, or if the
page throws. Lint (undefined or malformed words) is printed but doesn't fail the check. Set CHROME
to a Chrome/Chromium binary if one isn't found on the PATH.
"""
import html.parser, os, pathlib, re, shutil, subprocess, sys

CANDIDATES = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome',
              'chrome-headless-shell', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
FATAL = {'spec', 'duplicate', 'failure'}

class Report(html.parser.HTMLParser):
    """Collects the text of #report's summary and its rows as (kind, where, message)."""
    def __init__(self):
        super().__init__()
        self.depth = 0          # >0 while inside div#report
        self.summary, self.in_p, self.rows, self.row, self.cell = '', False, [], None, None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.depth:
            self.depth += tag == 'div'
            self.in_p |= tag == 'p'
            if tag == 'tr' and 'data-kind' in attrs: self.row = [attrs['data-kind']]
            if tag == 'td' and self.row is not None: self.cell = ''
        elif tag == 'div' and attrs.get('id') == 'report':
            self.depth = 1
    def handle_endtag(self, tag):
        if not self.depth: return
        if tag == 'div': self.depth -= 1
        if tag == 'p': self.in_p = False
        if tag == 'td' and self.cell is not None: self.row.append(self.cell.strip()); self.cell = None
        if tag == 'tr' and self.row is not None: self.rows.append(tuple(self.row)); self.row = None
    def handle_data(self, data):
        if not self.depth: return
        if self.cell is not None: self.cell += data
        elif self.in_p: self.summary += data

def main():
    page = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent.parent / 'index.html')
    chrome = os.environ.get('CHROME') or next((c for c in CANDIDATES if shutil.which(c) or os.path.exists(c)), None)
    if not chrome: sys.exit('No Chrome/Chromium found; set CHROME to its path.')
    run = subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--virtual-time-budget=5000',
                          '--dump-dom', page.resolve().as_uri()], capture_output=True, text=True, timeout=120)
    report = Report(); report.feed(run.stdout)
    # Uncaught exceptions, minus the ones the report already lists as spec errors.
    thrown = [f'{msg} (line {line})' for msg, line in re.findall(r'"(Uncaught [^"]*)", source: .*\((\d+)\)', run.stderr)
              if not any(msg in cells for kind, *cells in report.rows if kind == 'spec')]
    finished = report.rows or 'successfully validated' in report.summary

    print(' '.join(report.summary.split()) if finished else "The page's validator didn't finish running.")
    for kind, *cells in report.rows:
        print(f'  [{kind}] ' + ' — '.join(cells))
    for msg in thrown:
        print(f'  [thrown] {msg}')
    errors = sum(kind in FATAL for kind, *_ in report.rows) + len(thrown) + (not finished)
    lint = sum(kind == 'lint' for kind, *_ in report.rows)
    print(f'{errors} error(s), {lint} lint warning(s).')
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
