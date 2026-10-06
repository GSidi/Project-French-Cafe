# Task: write `backend/scripts/seed.py`

Written 2026-10-05. This is the entry point for step 4 (backend core loop).
Delete this file once `seed.py` works.

## Why this exists first

The read path (`GET /venues`) can't be tested against an empty database — a working
endpoint and a broken one both return `[]`. So: data first, then endpoints.

This is also the first code that imports the models and commits a transaction by hand,
rather than through Alembic or a FastAPI dependency.

## What to build

A standalone script (not an endpoint) at `backend/scripts/seed.py` that inserts:

- **3 venues** — different names. Leave `timezone` and `is_active` to their server defaults.
- **~6 tables per venue** — distinct `label`s, varied `seats`, `pos_x`/`pos_y` spread on a
  rough grid so the floor map has something to draw in step 5. Mix of `FREE` and `OCCUPIED`.

Two deliberate oddities in the data — put them in from the start, they are test fixtures:

- **One venue with zero tables.** This is the `LEFT JOIN` test case (an `INNER JOIN` would
  silently drop it) and the `200 []` test case for the tables endpoint.
- **One table with `is_active=False`.** Proves the count filter on `total_tables` works.

Prefer a list of dicts driving a loop over three pasted blocks. Copy-paste across
near-identical blocks is what produced both `claims` bugs on 2026-09-22.

## The insert pattern

```python
from app.database import SessionLocal
from app.models import Venue, Table, TableStatus

db = SessionLocal()
try:
    v = Venue(name="Café Grec", address="12 Rue Lafayette")
    db.add(v)
    db.flush()          # sends the INSERT now; v.id comes back populated

    db.add(Table(
        venue_id=v.id,
        label="T1",
        seats=4,
        pos_x=0,
        pos_y=0,
        status=TableStatus.OCCUPIED,
    ))

    db.commit()
finally:
    db.close()
```

Why it's written that way:

- **`flush()` not `commit()` mid-script.** `flush()` emits the pending SQL inside the open
  transaction and reads the generated `id` back into `v.id`, but commits nothing — a later
  exception still rolls everything back. One transaction, one `commit()` at the end.
  Committing per-venue leaves partial data behind if the script dies halfway.
- **You need `flush()` because you set `venue_id` by hand.** The models define no
  `relationship()`, so there is no `v.tables.append(...)` that would let SQLAlchemy order the
  inserts and fill the FK itself. Explicit FK ⇒ you need the real `id` first. Don't add
  relationships for this; they aren't needed yet.
- **`SessionLocal` has `autoflush=False`** (`app/database.py:13`) — nothing reaches the DB
  until you flush or commit. No implicit saves to reason about.
- **Pass the enum member** (`TableStatus.OCCUPIED`), never the string. A bare string coerces,
  but using the member is what stops the name==value trap recurring.
- **Don't pass `timezone` / `is_active` / `updated_at`.** They're `server_default`s; letting
  Postgres fill them is a test that the schema works. Consequence: after `flush()`,
  `v.is_active` is `None` in Python until refreshed — the value was computed in the database,
  not in this process.

`echo=True` is already set on the engine (`app/database.py:7`), so every INSERT prints.

## Three questions to answer yourself

Guess before looking anything up — the wrong guess is the useful part.

1. **How does `table.venue_id` get a value** when `Venue.id` is `Identity(always=True)` and
   doesn't exist until the INSERT runs? (Partly answered above — but be able to say *why*
   `flush()` makes the id appear and `add()` doesn't.)
2. **Should it be idempotent?** You will run it more than once. What happens on the second
   run, and what does `unique_tables_venue_label` do about it?
3. **How does `scripts/seed.py` find the `app` package** when you run it? Same class of
   problem as the Alembic `prepend_sys_path` gotcha, different cause. This one will announce
   itself immediately.

## Then

Show the script for review before moving on. After it works:

1. `GET /venues` — written the **naive** way first (loop, one count query per venue).
2. Count the `SELECT`s in the echo log. 3 venues → 4 queries. Add a venue → 5. That's N+1.
3. Rewrite as one `LEFT JOIN` + `GROUP BY`, watch the log collapse to one query.
4. `GET /venues/{id}/tables`, then `EXPLAIN` on it (the `WHERE venue_id = ?` / leading-prefix
   question from 2026-09-15).

## Design decisions already settled (don't relitigate)

- **`/venues` returns venue identity + `free_tables` / `total_tables`.** Named after the enum
  member `FREE`, not "available" — "available" drifts the moment `CLEARING` or `Claim` exists.
  `CLEARING` later just adds `clearing_tables`; nothing existing changes meaning.
- **Counts come from `tables.status`**, the denormalised column — not from `status_events`.
  This is that decision paying off: counting from the event log would need a per-table
  "latest event" window function on the hottest read path.
- **`is_active` filters belong in the count query** — an inactive table must not count toward
  `total_tables`, an inactive venue must not appear in the customer list.
- **Flat, not nested.** Tables are *not* embedded in `/venues`; that would carry every table
  of every venue, which is the payload the counts exist to avoid. `pos_x`/`pos_y` appear only
  on `/venues/{id}/tables`.
- **404 vs `200 []`** — venue doesn't exist → 404. Venue exists with no tables → `200 []`.
  So the service must check the venue exists as its own step; filtering tables by `venue_id`
  alone returns `[]` for both and the client can't tell them apart.
- **Stale counts are acceptable** (decided 2026-10-05). The venue list needs no push
  mechanism — refetch on open/focus is enough. This removes the venue list from step 7;
  WebSockets only need to cover the inside of a venue.
  **But:** that applies to *displaying* counts only. Deciding a staff toggle or a claim from a
  stale read is a bug — first-click-first-served depends on the compare-and-set being atomic.
  Same column, two different contracts.
