# Working on Papsa

- Max prefers sleek, self-documenting work and is wary of documentation bloat. Everything about Papsa
  itself lives in `index.html`. Don't write separate docs, or repeat here what the page already says.
- Run `python3 tools/check.py` before opening a PR (CI runs it too). It must report 0 errors, and a
  change shouldn't add lint warnings.
- Language design (vocabulary, grammar, semantics, phonology) is Max's call. Raise it as a GitHub issue
  and reply with an options memo before building: what's settled, what's open, options with example
  Papsa, and a recommendation. Mechanical fixes (consistency, typos, checks) can go straight to a PR.
- Older design notes are archived outside the repo. Ask Max if you need them.
