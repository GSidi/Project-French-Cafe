# Data Model — Database Schema

> **Purpose:** The single, concrete reference for the database structure. The high-level
> *reasoning* ("why this shape") lives in `PROJECT_BRIEF.md` §11; **this file is the detail** —
> tables, columns, types, keys, constraints, indexes.
>
> **How to use:** When adding or changing anything in the DB, update this file in the same change.
> Keep it in sync with the actual migrations. PostgreSQL types/conventions throughout.
>
> **Status:** v1 first draft. **Last updated:** 2026-07-15

---

## Conventions

- **Primary keys:** `id` — `BIGINT GENERATED ALWAYS AS IDENTITY` (simple, ordered). We can switch to
  UUIDs later if we ever expose ids publicly or need to merge datasets; not needed for v1.
- **Timestamps:** `TIMESTAMPTZ` (always timezone-aware — store UTC, render in the venue's tz).
  `created_at` / `updated_at` where useful.
- **Naming:** tables plural snake_case (`status_events`), columns snake_case, FKs `<entity>_id`.
- **Soft state:** use `is_active` flags rather than hard-deleting venues/tables (preserves history).

---

## Enums

```sql
-- Table status. v1 uses only FREE / OCCUPIED; later values reserved (see PROJECT_BRIEF §4).
CREATE TYPE table_status AS ENUM ('FREE', 'OCCUPIED');
-- Future: ALTER TYPE table_status ADD VALUE 'CLEARING';  (Postgres supports adding enum values)

-- Who/what caused a status change (for analytics + audit).
CREATE TYPE status_source AS ENUM ('staff_manual', 'system');
-- Future: ADD VALUE 'pos'  (when ordering-app / POS integration drives status)

-- User roles. No CUSTOMER in v1 (customers are anonymous — PROJECT_BRIEF §3.3).
CREATE TYPE user_role AS ENUM ('ADMIN', 'STAFF');

-- Claim lifecycle. v1: a claim is only ever ACTIVE then RELEASED; it holds nothing.
CREATE TYPE claim_status AS ENUM ('ACTIVE', 'RELEASED');
```

---

## Tables

### `venues`
A single cafeteria / bar.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | BIGINT | PK, identity | |
| name | TEXT | NOT NULL | Display name. |
| address | TEXT | | Free-form for v1. |
| timezone | TEXT | NOT NULL, default `'UTC'` | IANA tz (e.g. `Europe/Athens`); needed for correct analytics. |
| is_active | BOOLEAN | NOT NULL, default `true` | Soft on/off instead of delete. |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | |

### `tables`
A physical table within a venue. (Table name is `tables` — a bit meta, but clear.)

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | BIGINT | PK, identity | |
| venue_id | BIGINT | NOT NULL, FK → venues(id) | |
| label | TEXT | NOT NULL | e.g. "T3". Unique per venue (see index). |
| status | table_status | NOT NULL, default `'FREE'` | Current live status — the one hot value. |
| seats | SMALLINT | NOT NULL, default `2` | Capacity; used later for group filters (§9). |
| pos_x | INTEGER | NOT NULL, default `0` | Square floor-map grid position (§3.2). |
| pos_y | INTEGER | NOT NULL, default `0` | |
| is_active | BOOLEAN | NOT NULL, default `true` | |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()` | Bumped on every status change. |

**Concurrency (PROJECT_BRIEF §5):** claiming/toggling is a single-row conditional update, e.g.
```sql
UPDATE tables SET status = 'OCCUPIED', updated_at = now()
WHERE id = :id AND status = 'FREE';
-- rows affected = 1 → this caller won; = 0 → someone beat them to it.
```

### `status_events`
**Append-only** history — one row per status change. Never updated or deleted.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | BIGINT | PK, identity | |
| table_id | BIGINT | NOT NULL, FK → tables(id) | |
| old_status | table_status | | Null for the very first event, if any. |
| new_status | table_status | NOT NULL | |
| source | status_source | NOT NULL | What drove the change. |
| changed_by | BIGINT | FK → users(id), nullable | Which staffer (null if `system`). |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | The analytics time axis. |

> This table is expected to be the largest over time. It powers venue analytics (§8.3),
> audit, and future busyness prediction (§9). Cheap to write, impossible to backfill — hence in v1.

### `users`
Staff and Admin accounts only. **No customer rows in v1.**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | BIGINT | PK, identity | |
| email | TEXT | NOT NULL, UNIQUE | Login identity. |
| hashed_password | TEXT | NOT NULL | Never store plaintext; hash (e.g. bcrypt/argon2). |
| name | TEXT | | Display name. |
| role | user_role | NOT NULL | ADMIN or STAFF. |
| is_active | BOOLEAN | NOT NULL, default `true` | Disable without deleting. |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | |

### `staff_assignments`
Many-to-many join: which staff manage which venues.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | BIGINT | PK, identity | |
| user_id | BIGINT | NOT NULL, FK → users(id) | Should be a STAFF (or ADMIN) user. |
| venue_id | BIGINT | NOT NULL, FK → venues(id) | |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | |

Unique `(user_id, venue_id)` — no duplicate assignments (see index).

### `claims`
v1: a **log of a customer tapping "book."** Holds nothing, changes no table status.
Grows into real bookings later (will then gain a `user_id` FK once customers have accounts).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | BIGINT | PK, identity | |
| table_id | BIGINT | NOT NULL, FK → tables(id) | |
| status | claim_status | NOT NULL, default `'ACTIVE'` | v1 lifecycle is trivial. |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Lets us measure tap-interest per table. |

> **Deferred columns (do NOT add yet):** `user_id` (arrives with customer accounts + real booking),
> `expires_at` / hold logic (arrives when a claim actually reserves a table).

---

## Indexes (v1)

```sql
-- Fast "show me a venue's floor" (the hot customer read path).
CREATE INDEX idx_tables_venue ON tables (venue_id);

-- One label per venue.
CREATE UNIQUE INDEX uq_tables_venue_label ON tables (venue_id, label);

-- Analytics/audit reads: a table's history over time.
CREATE INDEX idx_status_events_table_time ON status_events (table_id, created_at);

-- No duplicate staff↔venue links.
CREATE UNIQUE INDEX uq_staff_assignment ON staff_assignments (user_id, venue_id);

-- Tap-interest lookups per table.
CREATE INDEX idx_claims_table ON claims (table_id);
```

---

## Entity relationship (quick view)

```
venues 1───N tables 1───N status_events
   │            │
   │            └──1───N claims        (v1: interest log; later: real bookings)
   │
   └──N───M users   (via staff_assignments)
```

---

## Change log
- **2026-07-15** — v1 first draft created.
