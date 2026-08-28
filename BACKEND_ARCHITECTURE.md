# Backend Architecture — How the Pieces Fit

> **Purpose:** Notes-to-self on how `backend/app/` is layered and *why*. Written 2026-08-26 while
> building the first ORM model. Companion to `DATA_MODEL.md` (which describes *what* the schema is;
> this describes *how the code is organised around it*).

---

## The three files, and the one thing each does

| File | Holds | Talks to Postgres? |
|---|---|---|
| `database.py` | `engine`, `SessionLocal`, `get_db` — the **connection** | **Yes.** The only one that does. |
| `base.py` | `Base` — the **registry** | No. |
| `models.py` | `Venue`, `User`, … — the **table definitions** | No. |

The common mix-up is thinking `base.py` is "the database." It isn't. It never opens a socket, never
reads `.env`, never needs Docker running.

There are really **two independent halves**:

- **A description of what the schema should look like** — `base.py` + `models.py`. Pure Python
  objects. Works with the database switched off.
- **A live connection to an actual Postgres** — `database.py`. Knows a host, port, and password.

They meet only when something needs to *do* a real thing (migrate, or query).

---

## `base.py` — the registry

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

Four lines, one job. `Base` is a **catalogue**.

When you write `class Venue(Base)`, the inheritance does something invisible: it registers `Venue`
into a shared collection hanging off `Base`, called **`Base.metadata`**.

Nothing else in the file. It imports one symbol from SQLAlchemy and nothing from our own code — that
is deliberate (see "Why `Base` gets its own file" below).

### Why `Base` gets its own file

Declaring `Base` inside `models.py` would work *today*. It's separated because of Alembic:

- Alembic's `env.py` needs to import `Base.metadata` to know the target schema.
- Every model module needs to import `Base` to define models.
- Other modules may need `Base` for type hints.

Keeping `Base` in a **leaf module that imports nothing of ours** means nothing can ever form an
import cycle around it. It's a tiny file whose entire job is to be safely importable from anywhere.

Related decision already made: **all models live in one `models.py`**, rather than one file per
model — same motivation, avoids Alembic circular-import pain.

---

## `models.py` — the table definitions

Each class is one table. Each `mapped_column` is one column. Still just a description — defining
`Venue` doesn't create anything in Postgres.

### The rule that keeps biting: two slots, two kinds of type

```python
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
#                  ^^^^^^^^                  ^^^^^^^^
#                  Python type               SQL type
```

- **Inside `Mapped[...]`** → the **Python** type the attribute holds at runtime.
  `int`, `str`, `bool`, `datetime`.
- **Inside `mapped_column(...)`** → the **SQL** type the column has in Postgres.
  `BigInteger`, `Text`, `Boolean`, `DateTime`.

**One-line rule: anything imported from `sqlalchemy` never goes inside `Mapped[...]`.**
Only builtins and stdlib types go there.

Wrong (all three of these were mistakes made while writing `Venue`):

```python
id:         Mapped[Identity]   # Identity is a SQLAlchemy construct
name:       Mapped[Text]       # Text is a SQLAlchemy type
created_at: Mapped[DateTime]   # DateTime is a SQLAlchemy type
```

Right:

```python
id:         Mapped[int]
name:       Mapped[str]
created_at: Mapped[datetime]   # from datetime import datetime
```

### The annotation also decides nullability

This is why you rarely need `nullable=`:

| Annotation | Column |
|---|---|
| `Mapped[str]` | `NOT NULL` |
| `Mapped[str \| None]` | nullable |

Passing `nullable=True` alongside `Mapped[str]` "works" but makes the type hint lie to you — the
editor thinks the value is never `None`. Let the annotation do the work.

### `server_default` is SQL, not Python

`server_default` emits DDL, so it takes a SQL-side value:

- A plain Python string is rendered as a **quoted literal** — `server_default="UTC"` → `DEFAULT 'UTC'`.
- For SQL keywords/functions use `text("true")` or `func.now()`, **not** Python `True`.

(`server_default="true"` on a boolean does work — Postgres coerces `'true'` — but `text("true")`
says what you mean.)

### `Identity`, the three orthogonal arguments

```python
id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
```

| Piece | Concern | Emits |
|---|---|---|
| `BigInteger` | how wide is the number | `BIGINT` |
| `Identity(always=True)` | who supplies the value | `GENERATED ALWAYS AS IDENTITY` |
| `primary_key=True` | is it the row's identity | `PRIMARY KEY (id)` |

Three separate concerns → three separate arguments. You could have an identity column that isn't a
primary key, or a primary key that isn't generated.

**`always=True` vs `always=False`:**

- `always=True` → `GENERATED ALWAYS`. Postgres **refuses** an INSERT supplying its own `id`.
- `always=False` → `GENERATED BY DEFAULT`. Postgres fills it in *unless* you supply one.

`always=True` is our default (and what `DATA_MODEL.md` specifies) because it makes a nasty bug
impossible: nobody can hand-pick an id, collide with the counter, and leave the sequence pointing at
an already-used number. That failure is invisible until the counter catches up, then *every* insert
starts failing with duplicate-key errors.

**Tradeoff:** it also blocks legitimate explicit ids — seed fixtures with known ids, or data imports.
Escape hatch when genuinely needed:

```sql
INSERT INTO venues (id, name) OVERRIDING SYSTEM VALUE VALUES (1, 'X');
```

**Why `Identity` and not `SERIAL`:** `SERIAL` is the pre-Postgres-10 way and is a fiction — it
expands into a separate sequence plus `DEFAULT nextval(...)`, only loosely attached to the column
(separate permissions, `ALTER TABLE` can orphan it, no `always` equivalent). `IDENTITY` is the
SQL-standard replacement where the sequence is genuinely owned by the column.

### At runtime

```python
v = Venue(name="Café Rue")   # note: no id
session.add(v)
session.flush()
print(v.id)   # 1
```

You never set `id`. SQLAlchemy omits it from the INSERT, and because it knows the column is
generated, appends `RETURNING id` and reads the value back into the object — no second query. That's
why `Mapped[int]` is honest even though you never assign it.

---

## `database.py` — the connection

```python
engine = create_engine(settings.database_url, pool_pre_ping=True, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- **`engine`** — the connection pool. One per app, created once at import.
- **`SessionLocal`** — a *factory*. CapWords deliberately: you call it like a constructor,
  `db = SessionLocal()`.
- **`get_db`** — FastAPI dependency. `yield` **pauses** the function so the `finally` runs *after*
  the endpoint returns; a `return` could never close the session. Sessions are **per-request**, not
  a shared singleton — that's about transaction isolation and `Session` not being thread-safe, not
  throughput.

---

## Where the two halves meet

Only at the moment something needs to act:

**Migrations (Alembic).** Reads `Base.metadata` (the *description*) and compares it against what
`engine` finds in the real database (the *reality*), then generates a migration for the difference.
Description on one side, connection on the other; Alembic is the bridge.

**Queries.** `db.query(Venue)` — the session (from `database.py`) supplies the connection; `Venue`
(from `models.py`) supplies the knowledge that `venues` has a `name` column of type `TEXT`. Neither
works alone.

```
base.py ──> models.py ──┐
 (Base)     (tables)    ├──> Alembic / queries ──> Postgres
                        │
database.py ────────────┘
 (engine, session)
```

---

## Inspecting `Base.metadata` yourself

`Base.metadata` is a real object you can poke at. No database connection needed — Docker can be off.

Run from the `backend/` directory using the venv interpreter:

```powershell
.\.venv\Scripts\python.exe
```

```python
import sys; sys.path.insert(0, '.')
from app.models import Venue          # importing registers the model
from app.base import Base

# 1. Which tables are registered?
Base.metadata.tables.keys()
# dict_keys(['venues'])

# 2. Inspect one table's columns
t = Base.metadata.tables['venues']
for c in t.columns:
    print(c.name, c.type, 'nullable=', c.nullable, 'pk=', c.primary_key)

# 3. The real payoff — print the exact DDL SQLAlchemy would emit
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
print(CreateTable(t).compile(dialect=postgresql.dialect()))
```

**Note:** you must `import app.models` first. `Base.metadata` is populated as a *side effect* of the
model classes being defined — import nothing, and it's empty.

**Watch the dialect.** Step 2 prints `created_at DATETIME` (SQLAlchemy's generic name); step 3
prints `TIMESTAMP WITH TIME ZONE` (what Postgres actually gets). Always trust the dialect-compiled
version — that's the real DDL.

### The self-check loop

After writing each model, print its DDL and diff it line-by-line against the matching table in
`DATA_MODEL.md`. That catches type/default/nullability mistakes without needing a review round-trip.

`venues` verified 2026-08-26:

```sql
CREATE TABLE venues (
	id BIGINT GENERATED ALWAYS AS IDENTITY,
	name TEXT NOT NULL,
	address TEXT,
	timezone TEXT DEFAULT 'UTC' NOT NULL,
	is_active BOOLEAN DEFAULT 'true' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id)
)
```

---

## Model build order

FKs force the sequence — each table can only reference ones already defined:

1. `venues` ✅ done 2026-08-26
2. `users` ← next (first `UNIQUE` constraint, first native PG enum)
3. `tables`
4. `staff_assignments`
5. `status_events`
6. `claims`

Then: Alembic init + first migration.
