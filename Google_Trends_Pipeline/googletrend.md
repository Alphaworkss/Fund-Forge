# How This Pipeline Works

A plain-language walkthrough of every file, for understanding — not just
running. `README.md` covers setup/usage; this covers the "why" behind
each piece of code.

## The big picture

Data flows through the files in one direction:

```
collect.py  →  clean.py  →  transform.py  →  storage.py
(get data)     (fix data)   (engineer         (save data)
                             features)
```

`pipeline.py` is the file that actually calls the other four in order.
`scheduler.py` calls `pipeline.py` on a timer. `test_pipeline.py` checks
that `clean.py`, `transform.py`, and `storage.py` behave correctly
without needing the internet.

Splitting it this way (instead of one big script) means each piece can
be tested, fixed, or swapped independently — e.g. if Google changes how
Trends works, only `collect.py` needs to change; `clean.py` and
`transform.py` don't care where the data came from.

---

## `collect.py` — getting the raw data

**Job:** ask Google Trends for search-interest numbers, hand back plain
Python dictionaries.

The `trendspy` library does the actual work of talking to Google.
`tr.interest_over_time(batch, timeframe=..., geo=...)` is the one call
that does it — it fetches and returns the data as a table (a pandas
DataFrame) with one row per date and one column per keyword.

(This used to go through `pytrends`, a two-step process of
`build_payload()` then `interest_over_time()`. That library's repo was
archived in 2025 and stopped working — Google changed its access-cookie
flow and pytrends never adapted — so this pipeline switched to trendspy,
which handles the current flow correctly.)

The function loops over `KEYWORDS` in groups of 5 (`BATCH_SIZE`) because
pytrends only accepts 5 keywords per request — that's a Google Trends
limit, not something we chose. For each batch, it converts the table
into a list of dictionaries like:

```python
{"keyword": "PSX", "date": "2026-07-15", "interest": 42, "is_partial": False}
```

`is_partial` comes from Google's own `isPartial` flag — it means "this
day/week isn't finished accumulating data yet, treat the number as
provisional." We keep track of it here so `clean.py` can decide to drop
it later.

`time.sleep(2)` between batches is just politeness — pausing briefly so
we don't hammer Google's servers with back-to-back requests, which is
also what makes rate-limiting less likely.

---

## `clean.py` — fixing the raw data

**Job:** take the list of dictionaries from `collect.py` and turn it
into a clean, reliable table.

Three specific problems it fixes, in order:

1. **Duplicates.** If the pipeline runs twice and both runs return data
   for the same keyword+date, `drop_duplicates(..., keep="last")` keeps
   only the most recent version instead of having two conflicting rows.

2. **Partial/incomplete data.** Rows where `is_partial` is `True` get
   dropped entirely (`df[~df["is_partial"]]`). The reasoning: an
   in-progress number is still changing, so anything computed from it
   (like a 7-day average) would later be wrong once the real number
   comes in.

3. **Data gaps disguised as zeros.** `s.mask(s == 0).ffill().fillna(0)`
   is doing something specific: it hides (`mask`) every `0`, then fills
   each hidden spot with whatever value came right before it
   (`ffill` = "forward fill"). If nothing came before it (i.e. the
   series starts with a gap), it falls back to `0`. This assumes an
   isolated `0` surrounded by real numbers is Google failing to report
   a value, not genuinely zero interest — reasonable for search
   interest, but worth knowing it's an assumption, not a certainty.

---

## `transform.py` — turning clean data into features

**Job:** take the clean table and compute the numbers the machine
learning model will actually use.

**Normalization** (`interest_norm`): Google's own 0–100 scale only
means "compared to other keywords in the *same request*" — it doesn't
mean much across different batches. So instead, each keyword is
rescaled against *its own* history:

```
(value - that keyword's minimum) / (that keyword's maximum - minimum)
```

This turns every keyword's series into its own 0-to-1 scale, where 0 is
"the lowest interest this term has ever had" and 1 is "the highest" —
comparable over time for that keyword, regardless of which batch it was
originally fetched in.

**Feature extraction** — three different lenses on the same number:

- `rolling_avg_7d`: the average of the last 7 *data points*. Smooths out
  noise so a single weird spike doesn't dominate.
- `pct_change_7d`: how much interest changed compared to 7 data points
  ago. Captures *momentum* — is interest rising or falling — which a raw
  level doesn't tell you.
- `zscore_30d`: how many standard deviations today's value is from the
  last 30 data points' average. This is an anomaly detector — a large
  positive or negative z-score means "today is unusual," which can be a
  more useful signal than the raw number itself.

**A subtlety worth knowing:** these names say "7d" and "30d" but they
count *data points*, not calendar days. Google Trends itself decides
the granularity of what it hands back based on how wide a window you
request — daily points for windows under ~9 months, weekly beyond that,
monthly beyond ~5 years. `collect.py` requests a rolling 2 years, which
crosses
that daily→weekly line, so right now these are actually ~7-week and
~30-week (~7 month) windows, not 7/30 days. The calculations themselves
are correct regardless — it's purely a naming/interpretation thing to
keep in mind when you use these features downstream.

---

## `storage.py` — saving everything

**Job:** define the database tables and provide simple save functions.

Two tables exist on purpose:
- `google_trends_raw` — closer to what was actually collected (still
  after cleaning, but before feature engineering). Useful if you ever
  need to recompute features differently without re-scraping.
- `google_trends_features` — the finished output other people's code
  (like the ML team's model) will actually read from.

Both use `PRIMARY KEY (keyword, date)`. Combined with
`ON CONFLICT(keyword, date) DO UPDATE SET ...`, this means: if a row for
that keyword+date already exists, *update* it instead of creating a
second one. That's what makes it safe to run the pipeline over and over
— nothing gets duplicated.

---

## `pipeline.py` — tying it together

**Job:** call the other files in the right order.

`run_once()` does exactly four things, in sequence: collect, save the
raw version, clean + transform, save the features. If `collect()`
returns nothing (e.g. a Google Trends failure), it logs a warning and
stops early rather than saving an empty/broken dataset.

This is the file you (or the scheduler) actually run — everything else
is a supporting piece it calls.

---

## `scheduler.py` — running it automatically

**Job:** call `pipeline.run_once()` right away, then again every day at
a fixed time, forever (until you stop it).

`schedule.every().day.at("08:00").do(job)` is the whole mechanism — the
`schedule` library just checks every minute (`time.sleep(60)`) whether
it's time to run the job yet.

---

## `test_pipeline.py` — proving it works

**Job:** check `clean.py`, `transform.py`, and `storage.py` behave
correctly, using made-up sample data instead of real Google Trends data.

Why fake data instead of real: tests need to be reliable and fast. If a
test depended on the internet, it could fail because Google is
rate-limiting you (not because your code is wrong), and it would be
slow. Testing the logic in isolation with known inputs means you know
exactly what the correct output should be, and can check for it.

Each test checks one specific behavior — e.g.
`test_clean_drops_partial_rows` only checks that partial rows disappear,
`test_storage_upsert_is_idempotent` only checks that saving the same
data twice doesn't create duplicates. Small, focused tests make it easy
to tell exactly what broke if one ever fails.