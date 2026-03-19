# 7-Day Quick Wins Plan

## Day 1
- Goal: make local and CI validation non-interactive
- Tasks:
  - add frontend ESLint config
  - add backend dev/test requirements or bootstrap notes
  - define standard local commands
- Expected output: repeatable lint/test entry points
- Owner type: full-stack/platform
- Measurable success: repo validates without setup prompts

## Day 2
- Goal: close obvious security footguns
- Tasks:
  - replace wildcard CORS
  - remove fallback default credentials in runtime services
  - tighten secret masking behavior
- Expected output: safer baseline runtime config
- Owner type: backend/security
- Measurable success: unknown browser origins rejected and missing secrets fail closed

## Day 3
- Goal: standardize user feedback
- Tasks:
  - add shared toast and confirmation dialog primitives
  - replace `alert`/`confirm` in key screens
- Expected output: accessible feedback layer
- Owner type: frontend
- Measurable success: no native browser dialogs on critical flows

## Day 4
- Goal: remove navigation friction
- Tasks:
  - fix or hide dead routes
  - add placeholder screens where necessary
  - add breadcrumb support
- Expected output: coherent navigation model
- Owner type: frontend/product
- Measurable success: zero broken top-level nav links

## Day 5
- Goal: improve data integrity
- Tasks:
  - add first index and constraint migration pack
  - document backfill approach
- Expected output: migration ready for review
- Owner type: backend/data
- Measurable success: key duplicates blocked and hot queries indexed

## Day 6
- Goal: improve diagnosability
- Tasks:
  - add structured request/run/task logs
  - standardize correlation IDs
- Expected output: usable operational log trail
- Owner type: backend/devops
- Measurable success: one run traceable end-to-end

## Day 7
- Goal: enforce the baseline
- Tasks:
  - add CI workflow for lint, type, build, and test smoke checks
  - add failure visibility to pull requests
- Expected output: first real quality gate
- Owner type: platform
- Measurable success: PRs fail on baseline regressions
