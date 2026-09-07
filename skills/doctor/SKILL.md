---
name: doctor
description: Check whether the advisor install actually works. Use when
  the user says "/doctor", "check if the advisor is working", "is my
  install ok", or similar troubleshooting requests. Free by default -
  only spends real money if the user explicitly asks for the full/live
  check.
---

# Check the advisor install

Two modes. Default is free (no advisor call). `--live` makes one real,
paid advisor call to prove the whole pipeline actually works, not just
that it looks configured. Only add `--live` if the user explicitly asks
for a full/live/real check - never add it "to be thorough" on your own.

## Find the script

This skill's own base directory, shown above when it loaded, is
`<plugin-root>/skills/doctor`. Drop the trailing `/skills/doctor` to get
`<plugin-root>` - the script is at `<plugin-root>/server/doctor.py`.

## Run it

Free check (default):
```
python3 <plugin-root>/server/doctor.py
```

Full check (only if the user explicitly asked - real cost):
```
python3 <plugin-root>/server/doctor.py --live
```

## Report the result

The output is already pass/fail per line - show it plainly, don't
summarize a FAIL away. If a line names the fix (e.g. "run /advisor-model
<model>"), say so; otherwise just report what's broken.
