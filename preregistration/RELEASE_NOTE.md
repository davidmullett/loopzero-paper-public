# Deviations log — release note

**2026-08-17: the OSF embargo was lifted; the V2 deviations & interpretations log is now public.**

`preregistration/DEVIATIONS.md` is released. Its SHA-256 is

```
9039c2179895807ce1081a3afb18b5380acc579f3219145d281b5c2b47fa8800
```

pinned in `preregistration/DEVIATIONS.sha256`. That hash was committed to the public
repository **before the controls sweep was run and before any decision quantity**
(ΔTPR, incremental AUC, the four criteria) was computed, so the log's pre-decision
dating is third-party provable and its contents are tamper-evident. Anyone can
reproduce it:

```
shasum -a 256 preregistration/DEVIATIONS.md
# → 9039c217…  — confirms the log is unaltered since the pre-decision commit
```

**Why the log's own header still reads as embargoed.** The header of `DEVIATIONS.md`
still states the file "stays local and gitignored … and cannot be published until the
OSF embargo lifts." That is the **original pre-decision text, deliberately left
unedited**: changing any byte would alter the file and break the `9039c217…` anchor
that is the tamper-evidence. Read the header as historical — the embargo has since
lifted (2026-08-17) and the log is published here unchanged.

**OSF pre-registrations (API-verified 2026-08-18).**

- Study 2 pre-registration: `osf.io/wka72` — a public OSF registration
  (`api.osf.io/v2/registrations/wka72/` → `public: true`, `registration: true`).
- Study 1 pre-registration: a frozen document in OSF **project** `osf.io/7bvgz`
  (`api.osf.io/v2/nodes/7bvgz/` → `public: true`, `registration: false`, `category: project`).
  The project's single registration is `wka72`.
