# Cafeteria Table Availability — Project Brief

> **Status:** Living document. Captures the core idea and grows as the project expands.
> Keep the core vision stable; append new detail under the relevant section rather than rewriting it.
>
> **Last updated:** 2026-07-14 (locked in tech stack: React+TS / FastAPI / PostgreSQL)

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
- Primary purpose: **see** availability (find a free spot).
- **Booking is a later feature.** For v1, tapping a free table leads to a simple
  **"Booked" placeholder screen** (a stub).
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

## 11. Open Questions / To Discuss
- **Technology stack** — next topic.
- Live-update mechanism (user's ideas).
- Real booking approach (own system vs. external redirect).
- What exact stats/management the Admin view needs.
```
