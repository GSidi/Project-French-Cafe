# Cafeteria Table Availability — Project Brief

> **Status:** Living document. Captures the core idea and grows as the project expands.
> Keep the core vision stable; append new detail under the relevant section rather than rewriting it.
>
> **Last updated:** 2026-07-15 (first-draft data model §11; anonymous-customer / stub-booking decision §3.3)

---

## 1. Vision

A **web app** (with a **mobile app** to follow) that shows **real-time table availability**
across **multiple cafeterias / bars**. The goal is simple and human: help a customer quickly
find a place to sit and grab a coffee, without walking in and discovering everything is full.

**Guiding principle:** Build the simplest version that works now, but design every piece to
leave room to expand. Always prefer the approach that keeps future options open.

---

## 2. Users & Roles

| Role         | What they do                                                                 |
|--------------|------------------------------------------------------------------------------|
| **Customer** | Browse all venues, see how many/which tables are free, tap a free table.     |
| **Staff**    | Manage the floor for *their own* venue — update table status.                |
| **Admin**    | Manage venues, tables, and staff accounts across all locations; view stats.  |

```
Admin    → manages venues, tables, staff accounts (all locations)
Staff    → updates table status for THEIR venue
Customer → browses all venues, sees table availability
```

---

## 3. Core Features

### 3.1 Multi-venue
- The platform hosts **many** cafeterias / bars from day one.
- Customers can check availability at **each** venue.

### 3.2 Venue floor view
- A **simple square-type floor map**: tables shown as shapes, colored by status
  (e.g. free = green, occupied = red).
- Generic layout for now — **not** a real per-café map yet. Refine later.

### 3.3 Availability & booking
- Primary purpose: **see** availability (find a free spot). **Anyone — including
  anonymous, not-logged-in users — can browse all venues and see availability.**
- **Booking is a later feature.** For v1, tapping a free table shows a simple
  **✓ + small "Booked" confirmation** (a stub). Crucially, this stub **holds nothing**:
  it does **not** change the table's status and does **not** reserve it. Two customers
  can both tap the same free table and both walk over — exactly like the world works
  today with no app. The atomic-claim machinery (§5) is still built and ready, just not
  wired to a real hold yet.
- **Real booking (holding a table) is gated behind having an account.** Rationale: a real
  reservation is a *commitment against a scarce resource*; without an account there is no
  accountability, and anonymous ghost-holds would make the map lie (the make-or-break risk,
  §8.1). So: **everyone can see; only account-holders will (later) truly book.** In v1 nobody
  truly books — the tap is a stub — so **v1 needs no customer accounts.** Staff/Admin still
  log in.
- Future options for real booking (decision deferred):
  - Redirect to the specific café's external booking site, **or**
  - Provide our **own** booking system (would need to be built).

---

## 4. Table Lifecycle

**Full future lifecycle:**

```
FREE → (seated / order taken) → OCCUPIED → (paid) → CLEARING → (staff clears) → FREE
```

- The **`CLEARING`** state solves the real-world "customer paid early but is still sitting"
  problem — a table isn't truly free until it's physically cleared.
- Long-term, status is driven by the **staff ordering app** (ties status to physical reality,
  which is accurate and resistant to abuse like ghost reservations).
- Possible future augmentation: external **live-busyness data (e.g. Google)** as an
  *additional* signal for occupancy — exploratory, "maybe."

**v1 (current scope):** Staff **manually toggle** tables between **FREE** and **OCCUPIED**.
Richer states (`CLEARING`, ordering-app integration) come later — but the data model is
designed now to accommodate them.

---

## 5. Concurrency (two+ customers claim the same table)

**Decided approach: first-click-first-served via atomic compare-and-set.**

- The **server is the single source of truth.**
- Claiming a table is a **conditional update**: "set to reserved **only if** currently free."
- First request wins; the second fails **gracefully** → customer sees
  "Sorry, that table was just taken" and the map refreshes.
- Standard *optimistic concurrency* — a proven, low-effort solution.

---

## 6. Live Updates
- Live/real-time availability is **desired**.
- Exact mechanism is **TBD** — dedicated discussion later (the user has ideas).

---

## 7. Scope Summary

### In scope for v1
- Multi-venue browsing (customer).
- Simple square floor map per venue with table statuses.
- Staff view: manual FREE ⇄ OCCUPIED toggle.
- Customer taps free table → "Booked" stub screen.
- Admin: manage venues, tables, staff.
- Concurrency handled correctly (atomic claim).

### Deferred / future
- Real booking system (own or external redirect).
- Full table lifecycle (`OCCUPIED → CLEARING → FREE`).
- Staff ordering app / **POS integration** as the status driver.
- External live-busyness data (e.g. Google) as an extra signal.
- Native mobile app.
- True live/real-time update mechanism.

---

## 8. Key Risks & Strategy

> The software is the easy part. Success depends on solving these, not on features.

### 8.1 Data accuracy is everything (the make-or-break risk)
- The app is only valuable if availability shown is **true**. A map that lies loses users
  permanently after one bad experience.
- **Manual staff tapping fails at rush hour** — exactly when the data matters most, staff are
  too busy to update it, so the data rots when it's needed.
- **Therefore the real heart of the product is POS / ordering-app integration**, which makes
  accuracy a *byproduct* of work staff already do — not extra work. This matters more than the
  customer-facing map itself.

### 8.2 Cold-start / chicken-and-egg
- Two-sided: customers need many venues onboard; venues need customers. Classic marketplace
  cold-start.
- **Strategy: go hyper-local first** — dominate one campus / neighborhood / food court before
  expanding. Not "all cafés everywhere" on day one.

### 8.3 Business model (shapes what we build)
- Likely payer = **venues** (subscription for staff tools + floor analytics).
- Customer app stays **free** — it's the *magnet*; the venue tools are the *product*.
- Implication: invest early in tools/insights venues will pay for.

### 8.4 Product discipline
- **Nail one loop first:** *customer opens app → sees a truly-free table → goes → it's actually
  free* — for **one venue**. Everything else is decoration until that loop is trustworthy.
- Keep v1 ruthlessly small; **record** ambitious ideas (below) without building them yet.

---

## 9. Future Ideas (record, don't build yet)

Kept here to keep the vision ambitious without bloating v1.

- **Wait-time / busyness prediction** ("usually quiet around 3pm") — often more useful than exact
  table counts; users already expect this from Google.
- **Favorites + notifications** ("a table just opened at your usual spot").
- **Table-attribute filters** — power outlet, window, quiet zone, big group, laptop-friendly.
  Real unmet need for students / remote workers.
- **Ordering / pre-order + pay** — natural extension of POS integration; also a revenue path.
- **Venue analytics dashboard** — peak times, table turnover. Venues may pay more for insight
  into their own floor than for the customer map.
- **Loyalty / check-in rewards** — pull customers back.

---

## 10. Technology Stack (decided)

> **Locked in.** Rationale recorded so future-us remembers *why*.

| Layer | Choice |
|---|---|
| **Frontend (web)** | **React + TypeScript** (Vite) |
| **Backend** | **FastAPI (Python)** — modular monolith (not microservices) |
| **Database** | **PostgreSQL** |
| **Live updates** | **WebSockets** (FastAPI async-native) |
| **Mobile (future)** | React Native / Expo — reuses React knowledge |

### Why FastAPI / Python (not Java, Django, or microservices)
- **Team is 1–2 people** → optimize for **velocity and shipping the core loop**, not for
  large-team/large-codebase robustness (which is where Java's compile-time safety shines).
- User already knows **Python**; only the *framework* is new. FastAPI is one of the gentler
  ones to learn, has **async-native WebSockets** (fits live updates), auto-generated API docs
  (helps the React frontend + future POS integration), and minimal boilerplate.
- **Modular monolith, not microservices:** microservices solve big-org/scale problems we don't
  have; they'd add heavy ops complexity against §8.4 "keep v1 tiny." Design clean internal
  modules now so we *can* split later if ever needed.

### Honest trade-off (accepted)
- Python's dynamic typing is a weaker long-run safety net than Java at large scale. **Mitigation:**
  use type hints everywhere, Pydantic for validation, write tests, keep modules clean.
- If this ever becomes a big-team, payments-heavy platform, the core *could* be rewritten on the
  JVM later — a "good problem to have," and the modular design avoids a from-scratch rewrite.
- Keep the door open for a **future Python ML/analytics service** if the busyness-prediction
  idea (§9) arrives — Python is ideal there.

### Learning note
- User knows **core Python** but is new to FastAPI and modern web stacks (React/TS). Teach the
  web-specific concepts step by step; don't assume framework knowledge.

---

## 11. Data Model (v1)

> First-draft entity design. Kept deliberately small, but each choice leaves room to expand.
> **Concrete schema** (column types, keys, constraints, indexes) lives in **`DATA_MODEL.md`** —
> keep the two in sync; this section is the *why*, that file is the *detail*.

### Entities

```
Venue ──1:N── Table ──1:N── StatusEvent (append-only history)
  │             │
  │ N:M         │ 1:N
  │             │
User ─(StaffAssignment)      Claim (v1: a log of taps, holds nothing)
```

| Entity | Key fields | Notes |
|---|---|---|
| **Venue** | id, name, address, timezone, is_active | A cafeteria/bar. `timezone` matters for analytics (§8.3). |
| **Table** | id, venue_id (FK), label, status, seats, pos_x, pos_y, updated_at | `status` = enum (v1: `FREE`/`OCCUPIED`). `pos_x/pos_y` = square floor-map position (§3.2). |
| **StatusEvent** | id, table_id (FK), old_status, new_status, changed_by, source, created_at | **Append-only.** Written on every status change. Powers venue analytics + audit + future busyness prediction. |
| **User** | id, email, role, hashed_pw, name | Roles: Admin / Staff. (No Customer accounts in v1 — customers are anonymous.) |
| **StaffAssignment** | id, user_id (FK), venue_id (FK) | **Many-to-many** join: a staffer can cover multiple venues, a venue can have many staff. |
| **Claim** | id, table_id (FK), created_at, status | v1: a **log of a customer tapping "book"** — does NOT change table status or reserve. Grows into real bookings later (will then carry a `user_id`). |

### Decisions locked in (with why)
- **`Table.status` is a column, not a table** — one current value per table; makes the atomic
  claim (§5) a cheap single-row conditional `UPDATE`.
- **`status` is an enum, not a boolean** — leaves room for `CLEARING` + ordering-app states (§4)
  without changing the data's meaning.
- **`StatusEvent` ships in v1** — near-zero cost now; history can't be backfilled later, and it's
  the raw material for the analytics venues will *pay* for (§8.3).
- **Staff↔Venue is many-to-many** — matches the multi-venue vision; avoids a painful migration if a
  manager ever covers two venues.
- **Customers are anonymous in v1** — see §3.3. Accounts arrive bundled with *real* booking.
- **`Claim` exists but holds nothing in v1** — gives the concurrency logic something real to write
  later and grows into real bookings; for now it's just an interest log.

### Still open at the data-model level
- Should `Claim` be in v1 at all, or added only when real booking lands? (Leaning: include a minimal
  version — cheap, and it lets us measure tap-interest.)
- Exact `source` values for `StatusEvent` (e.g. `staff_manual`, later `pos`, `system`).

---

## 12. Open Questions / To Discuss
- Live-update mechanism (user's ideas).
- Real booking approach (own system vs. external redirect).
- What exact stats/management the Admin view needs.
```
