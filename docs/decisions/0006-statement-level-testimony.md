# ADR-006: Witness questions unlock individual statements

- Status: **Accepted**
- Date: 2026-10-22

## Decision

Focused questions grant only matching authored statements and their leads to the
investigator's knowledge. Filtering just the displayed answer while recording
the entire account makes follow-up questions unnecessary and exposes unasked
testimony to the casebook and Narrator.

A general interview returns the first authored statement as an opening. Repeating
that request returns the same opening rather than draining the account. Explicit
topics match meaningful words in authored statements or lead keys, deterministically.
Empty and unsupported topics return no statements or leads. There is no model
selection of truth and no automatic grant for an "everything" topic.

## Knowledge and persistence

Each mutable conversation record holds the testimony keys this investigator has
heard. Subsequent questions add keys without removing prior knowledge or changing
canonical testimony. The handler selects statements before building its mutation
plan; the public projection reads only recorded keys. Casebook, lead review,
remembered testimony, and Narrator focus share that projection.

Old conversation records without `testimony_keys` retain their prior full-account
knowledge (`None`); new records always store a tuple, including an empty tuple
when nothing was answered. Later focused questions never erase legacy knowledge.
No canonical case schema or facts change, and accusation rules still depend on
examined physical evidence.

## Limits

Topic matching currently uses authored wording and lead keys, not semantic
inference or an exhaustive topic menu. Optional authored aliases can follow
playtesting. Public suggestions must not expose topics from unheard testimony.
The localhost browser host still has no save/resume UI; the compatibility policy
applies to the existing ECS save/load path.
