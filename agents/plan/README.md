# NutriPlan AI — Agent Delivery Plan

## Overview

This folder contains the week-by-week delivery plan for NutriPlan AI. Each file is a standalone brief for the Developer agent — everything needed to build and verify that week's deliverables.

| Week | File | Focus |
|---|---|---|
| 1 | [WEEK_1.md](WEEK_1.md) | Backend foundation + Supabase Auth + patient CRUD + frontend login/dashboard |
| 2 | [WEEK_2.md](WEEK_2.md) | Mistral OCR pipeline + Medical Profile Builder + Pinecone/pgvector embeddings |
| 3 | [WEEK_3.md](WEEK_3.md) | GPT-4o diet plan generation + allergen guard + no-repeat validator + macro scaling |
| 4 | [WEEK_4.md](WEEK_4.md) | Full frontend UI: 7-step patient wizard, plan review, MacroSlider, PDF export |
| 5 | [WEEK_5.md](WEEK_5.md) | Docker, Nginx, GitHub Actions CI/CD, AWS ECS Fargate, CloudFormation |

## Rules

1. A week is not complete until **all acceptance criteria are ticked**.
2. `PROGRESS.md` must be updated at the end of every working session.
3. No secrets in any file committed to the repository.
4. Each week's code must pass its tests before moving to the next week.
5. The Team Lead reviews code at the end of each week — never skip this step.

## Agent Roles

- **Developer** — implements features, writes tests, self-reviews before handoff (see `DEVELOPER.md`)
- **Team Lead** — reviews code quality, security, and robustness after each week (see `TEAM_LEAD.md`)
