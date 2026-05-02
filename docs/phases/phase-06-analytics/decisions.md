# Decisions

## Decision Log
- Date: 2026-05-02
  - Decision: Implement analytics as API aggregations over operational database.
  - Context: Immediate visibility was required without introducing a new data platform.
  - Impact: Faster delivery with manageable query complexity.

- Date: 2026-05-02
  - Decision: Keep analytics endpoints separated by domain (dashboard vs fraud).
  - Context: Different teams consume different metric sets.
  - Impact: Cleaner API contracts and simpler frontend composition.

- Date: 2026-05-02
  - Decision: Prioritize operationally actionable metrics over exhaustive BI outputs.
  - Context: Primary users are switch/fraud operations teams.
  - Impact: Current analytics focuses on counts, trends, and breakdowns needed for daily monitoring.
