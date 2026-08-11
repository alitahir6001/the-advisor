#!/usr/bin/env python3
"""Read the advisor consult log.

  python3 ~/.claude/advisor/consults.py            # recent consults, one line each
  python3 ~/.claude/advisor/consults.py -n 20      # last 20
  python3 ~/.claude/advisor/consults.py 3          # full entry #3 (question, context, reply)
  python3 ~/.claude/advisor/consults.py --stats    # counts by provider/day
"""

import json
import os
import sys
from collections import Counter

LOG = os.environ.get("ADVISOR_LOG") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "consult-log.jsonl"
)


def load():
    if not os.path.exists(LOG):
        sys.exit(f"no consult log yet at {LOG}")
    out = []
    for line in open(LOG):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def one_line(i, e):
    when = e["ts"][:16].replace("T", " ")
    mark = "ok" if not e.get("error") else "ERR"
    q = " ".join(e.get("question", "").split())
    return f"[{i}] {when}  {e['provider']:<14} {e['elapsed_s']:>5}s  {mark}  {q[:90]}"


def show(e):
    print(f"when:     {e['ts']}")
    print(f"provider: {e['provider']}  model: {e.get('model')}  {e['elapsed_s']}s")
    for field in ("question", "context", "reply", "error"):
        if e.get(field):
            print(f"\n--- {field} ---\n{e[field]}")


def main():
    args = sys.argv[1:]
    entries = load()

    if "--stats" in args:
        print(f"{len(entries)} consults in {LOG}\n")
        for label, key in (("provider", "provider"), ("day", None)):
            counts = Counter(
                e[key] if key else e["ts"][:10] for e in entries
            )
            print(f"by {label}:")
            for k, v in sorted(counts.items()):
                print(f"  {k:<16} {v}")
            print()
        errs = [e for e in entries if e.get("error")]
        if errs:
            print(f"errors: {len(errs)} (latest: {errs[-1]['error'][:80]})")
        return

    if args and args[0].isdigit():
        idx = int(args[0])
        if not 0 <= idx < len(entries):
            sys.exit(f"no entry {idx} (have 0-{len(entries)-1})")
        show(entries[idx])
        return

    n = int(args[args.index("-n") + 1]) if "-n" in args else 10
    for i, e in list(enumerate(entries))[-n:]:
        print(one_line(i, e))


if __name__ == "__main__":
    main()
