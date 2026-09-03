# Project 03 — Operational Reporting & SQL Performance Engineering

## Project Summary

This project demonstrates a complete SQL Server reporting-engineering workflow built around a synthetic operational dataset.

The central challenge was to produce a reporting dataset with:

> **one row per PersonID**

while preserving multiple cases, multiple offenses, date/offense filtering, deterministic address selection, and SSRS-ready output.

The project evolved from a straightforward relational join into a validated, benchmarked, report-ready solution.

---

## The Problem

The source model contains several one-to-many relationships:

```text
Person
  → Cases
  → Offenses

Person
  → Addresses
```

A direct join can therefore expand toward:

```text
Person × Case × Offense × Address
```

That produces valid relational rows, but not the required reporting grain.

In the development dataset, the baseline join returned:

| Metric | Result |
|---|---:|
| Joined rows | 5,340 |
| Distinct qualifying people | 1,971 |
| Extra rows beyond person grain | 3,369 |
| Average rows per person | 2.71 |

The key lesson was that `DISTINCT` alone could not solve the problem because the duplicated report profiles were being produced by legitimate lower-grain business relationships.

---

## Engineering Approach

The final design follows a deliberate sequence:

```text
filter qualifying cases/offenses
        ↓
establish qualifying people
        ↓
materialize Person × Case
        ↓
materialize Person × Offense
        ↓
aggregate case/offense history
        ↓
choose one deterministic address
        ↓
assemble final PersonID-grain dataset
```

This separates relational complexity from report presentation and ensures that every working set has an explicit, known grain.

---

## Materialization and Repeated Work

The first grain-correct redesign produced the correct result, but performance testing revealed expensive repeated aggregation work.

The improved design materialized reusable intermediate sets such as:

```text
#PersonCases
    PersonID × CaseID
```

and:

```text
#DistinctPersonOffenses
    PersonID × OffenseGroup × OffenseType
```

These tables were indexed around the repeated lookup key:

```text
PersonID
```

This reduced repeated reconstruction of underlying joins and eliminated the large Worktable activity observed in the earlier version.

---

## Targeted Source Indexing

Three nonclustered source-table indexes were added based on actual access patterns:

### Cases

Supports the report date-range predicate and downstream CaseID join.

### Offenses

Supports offense-group filtering and the CaseID relationship.

### Addresses

Supports PersonID lookup and deterministic current-address ranking.

The project deliberately avoided adding redundant indexes where existing clustered keys already supported the query path.

---

## Benchmark Results

At benchmark scale, the source-index comparison produced the following logical-read reductions:

| Source table | Without project indexes | With project indexes | Reduction |
|---|---:|---:|---:|
| Cases | 798 | 60 | 92.5% |
| Offenses | 2,795 | 1,081 | 61.3% |
| Addresses | 306 | 250 | 18.3% |
| **Combined** | **3,899** | **1,391** | **64.3%** |

The strongest improvement occurred on date-filtered case retrieval.

The headline benchmark result is:

> **64.3% fewer combined logical reads across the three indexed source tables.**

---

## Correctness Validation

Performance improvements were accepted only after validating that the business result remained correct.

On the benchmark dataset:

| Validation Metric | Result |
|---|---:|
| Final rows | 13,129 |
| Distinct qualifying people | 13,129 |
| Duplicate PersonIDs | 0 |
| Missing qualifying people | 0 |
| Unexpected people | 0 |
| Date-filter violations | 0 |
| Offense-filter violations | 0 |

Additional validation confirmed:

- multi-case people remained represented once;
- multi-offense people remained represented once;
- case counts reconciled to source relationships;
- offense counts reconciled to source relationships;
- most-recent case dates reconciled;
- selected addresses matched the intended ranking rule;
- people without addresses remained in the final report;
- concatenated case and offense histories remained complete.

---

## SSRS Delivery

The final query was adapted for SSRS with parameters for:

```text
Start Date
End Date
Offense Group
```

The dataset remains:

> **one row per PersonID**

which keeps the report layer simple.

SSRS is used for:

- profile-card layout;
- parameter selection;
- page headers/footers;
- pagination;
- print/PDF delivery.

Relational aggregation and deduplication remain in SQL.

---

## Reporting Design

The report design uses a repeating person-profile card containing:

- display name;
- PersonID;
- date of birth;
- gender;
- photo status;
- selected address;
- qualifying case count;
- most recent case date;
- regions;
- offense groups;
- offense types;
- qualifying case numbers.

The design is intended to support both screen review and print/PDF use.

---

## Performance-Testing Approach

The project emphasized repeatable engineering evidence rather than one-off elapsed-time claims.

Primary measures included:

- logical reads;
- physical reads;
- CPU time;
- repeated benchmark runs;
- output reconciliation.

A later cold-vs-warm execution check also demonstrated that cached data pages can materially affect physical I/O while leaving logical reads largely unchanged.

---

## Key Engineering Lessons

### Define grain before tuning

The required output grain must be explicit before optimization begins.

### Correct SQL is not automatically efficient SQL

A query can return the right answer and still perform unnecessary repeated work.

### Materialize when repeated access is expensive

Temporary tables can be valuable when a reusable intermediate grain benefits from statistics and indexing.

### Index for access patterns

Useful indexes reflect filtering, join direction, ordering, and coverage—not merely the presence of a column in a JOIN.

### Measure before changing the design

Performance tuning should follow:

```text
observe
→ measure
→ hypothesize
→ redesign
→ benchmark
→ validate
```

### Validate after every optimization

A faster query is not an improvement if it changes the business result.

---

## Portfolio Outcome

This project demonstrates experience with:

- SQL Server relational modeling;
- grain and cardinality control;
- one-to-many relationship management;
- temporary-table materialization;
- clustered and nonclustered indexing;
- logical-read benchmarking;
- performance diagnostics;
- correctness reconciliation;
- SSRS dataset design;
- parameterized operational reporting;
- print/PDF-oriented report delivery.

---

## Final Principle

> **Correct grain first. Measure second. Optimize deliberately. Validate again. Present last.**
