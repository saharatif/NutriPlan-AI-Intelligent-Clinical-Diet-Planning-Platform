# NutriPlan AI — Pre-Production Guidelines

**Last updated:** 2026-05-24  
**Target deployment:** AWS ECS Fargate via CloudFormation (Week 5)

---

## Purpose

This document defines the checks, configuration steps, and release criteria that must be satisfied before the application is deployed to a production environment. Do not bypass or abbreviate these steps — NutriPlan handles clinical patient data.

---

## 1. Environment Configuration

### 1.1 Secrets

All secrets must be in AWS Secrets Manager before deployment. Zero secrets may appear in:
- CloudFormation templates or parameter files
- Docker images or build args
- GitHub Actions secrets as plaintext strings (use OIDC, not access keys)
- CI logs (set `no-mask: false` on any step that echoes env vars)

Required secrets in Secrets Manager:

| Secret Name | Value source |
|---|---|
| `nutriplan/OPENAI_API_KEY` | OpenAI dashboard |
| `nutriplan/MISTRAL_API_KEY` | Mistral console |
| `nutriplan/SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API |
| `nutriplan/SUPABASE_JWT_SECRET` | Supabase → Settings → API |
| `nutriplan/DATABASE_URL` | Supabase → Settings → Database → URI |
| `nutriplan/REDIS_URL` | ElastiCache endpoint or Upstash URL |
| `nutriplan/PINECONE_API_KEY` | Pinecone console (only if `VECTOR_BACKEND=pinecone`) |

### 1.2 Production environment variables

Set in the ECS Task Definition (not Secrets Manager — these are not sensitive):

```
DEBUG=false
VECTOR_BACKEND=pgvector
DIET_PLAN_GENERATION_PROVIDER=openai
OPENAI_DIET_MODEL=gpt-4o
```

### 1.3 `.env` audit

Before any release branch is cut, run:

```bash
git check-ignore .env
git log --all --full-history -- "*.env" | head -5
```

If `.env` or any file containing a real API key appears in git history, treat it as a credential leak and rotate all affected keys immediately.

---

## 2. Database

### 2.1 Migrations

```bash
# Verify migration history is clean
alembic history --verbose

# Apply all pending migrations
alembic upgrade head

# Confirm current head
alembic current
```

Never run `alembic downgrade` against the production database without an explicit rollback plan and a recent backup.

### 2.2 RLS policies

Row-Level Security must be active on all patient tables. Verify in the Supabase SQL Editor:

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

All patient tables must show `rowsecurity = true`. If any show `false`, re-apply the policies from `backend/db/schema.sql` before proceeding.

### 2.3 pgvector extension

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

Must return a row. If not, run `CREATE EXTENSION IF NOT EXISTS vector;` in Supabase SQL Editor.

---

## 3. Backend Release Checklist

- [ ] All 20+ backend tests pass: `pytest tests/ -v --tb=short`
- [ ] No test is marked `skip` or `xfail` without an accompanying ticket
- [ ] `DEBUG=false` in production config — verify `config.py` reads this correctly
- [ ] Rate limiting is active — `slowapi` is wired in `main.py`
- [ ] Audit logging is enabled — all doctor actions write to `audit_logs`
- [ ] Celery task modules registered explicitly in `celery_app.py` (not autodiscover)
- [ ] `ocr_service.py` BUG-006 status reviewed — pipe-delimited table markers may still be missed
- [ ] WeasyPrint PDF export tested end-to-end with a real patient record

---

## 4. Frontend Release Checklist

- [ ] `npx tsc --noEmit` exits with zero errors
- [ ] `npm run build` completes without warnings in `dist/`
- [ ] No `console.log` or `console.error` in production code (except error boundaries)
- [ ] No hardcoded localhost URLs in `api.ts` or `supabase.ts`
- [ ] `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set in the frontend build environment — **only** these two vars, never the service role key
- [ ] All 7 patient wizard steps tested end-to-end in a browser
- [ ] Diet plan calendar renders correctly and meal slot colours display as intended
- [ ] PDF export opens in browser and shows correct patient name and allergen banner

---

## 5. Security Checklist

- [ ] `.env` is in `.gitignore` — confirmed by `git check-ignore .env`
- [ ] No secrets in CloudFormation template or `parameters.*.json`
- [ ] GitHub Actions uses OIDC role assumption — no `AWS_ACCESS_KEY_ID` stored as a secret
- [ ] Supabase Storage bucket `patient-documents` is set to **Private** — access via signed URLs only
- [ ] Nginx security headers are set in `nginx/nginx.conf`:
  - `X-Frame-Options DENY`
  - `X-Content-Type-Options nosniff`
  - `Referrer-Policy strict-origin-when-cross-origin`
- [ ] structlog is confirmed not logging request bodies or patient PII — only UUIDs in log fields
- [ ] RLS integration test passes (second doctor cannot read first doctor's patients)
- [ ] Supabase ES256 JWKS verification is active in `deps.py` — do not revert to HS256-only

---

## 6. Infrastructure (AWS)

### 6.1 Before deploying the CloudFormation stack

- [ ] ECR repositories created: `nutriplan-backend`, `nutriplan-frontend`, `nutriplan-worker`
- [ ] Docker images built and pushed to ECR with a versioned tag (not `latest`)
- [ ] Secrets Manager secrets populated (see Section 1.1)
- [ ] VPC with at least two AZs and public subnets available (or use default VPC)
- [ ] ACM certificate issued and validated if using HTTPS

### 6.2 Deploy

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/template.yml \
  --stack-name nutriplan-ai \
  --parameter-overrides file://infra/cloudformation/parameters.dev.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### 6.3 Post-deploy smoke tests

After the ALB DNS name is available:

```bash
# Health check
curl https://<alb-dns>/health

# Expected: {"status": "ok", "version": "...", "timestamp": "..."}
```

Then perform a full manual test in the browser:
1. Register a new doctor account
2. Create a patient with at least 2 conditions, 2 allergens, and 1 medication
3. Upload a blood-test PDF and confirm OCR completes
4. Generate a diet plan and confirm 28 days × 4 meals = 112 meals
5. Approve the plan and export the PDF diet chart

### 6.4 Monitoring

Verify CloudWatch log groups are receiving data:

```
/nutriplan/backend
/nutriplan/frontend
/nutriplan/worker
```

Set a billing alarm at $20/month before leaving the stack running.

---

## 7. Rollback Procedure

### Application rollback

Re-deploy the previous ECR image tag:

```bash
aws cloudformation deploy \
  --stack-name nutriplan-ai \
  --parameter-overrides ImageTag=<previous-tag>
```

### Database rollback

```bash
alembic downgrade -1
```

Only safe if the code change was forward-compatible. If data was written in the new schema, restore from a Supabase backup instead.

### Full teardown

```bash
aws cloudformation delete-stack --stack-name nutriplan-ai
```

This removes all ECS services, the ALB, and IAM roles. It does not delete the Supabase project, Pinecone index, or ECR repositories.

---

## 8. Known Risks Before Production

| Risk | Severity | Status |
|---|---|---|
| BUG-006: Mistral pipe-delimited blood markers not parsed | Major | Open — some markers (e.g. ESR) silently dropped from `blood_test_results` |
| Week 5 infrastructure not built | Blocker | Dockerfiles, CI, and CloudFormation are unwritten |
| Frontend Node.js broken on original dev machine | Minor | Use Docker or a clean Node 20 install |
| OCR quality varies by PDF format | Medium | Only tested on Neelam Ashok Bharwani's report (15 pages, 109 markers) |
| GPT-4o cost at scale | Medium | No per-doctor or per-month spending caps configured |
| Pinecone index not seeded | Low | pgvector is the default — Pinecone only activates with `VECTOR_BACKEND=pinecone` |

---

## 9. Release Sign-Off

All of the following must be confirmed before traffic is routed to the production environment:

- [ ] All backend tests passing
- [ ] TypeScript zero errors, frontend builds cleanly
- [ ] Security checklist complete (Section 5)
- [ ] Database migrations applied and RLS verified
- [ ] AWS stack deployed and smoke tests passed
- [ ] CloudWatch logs confirmed flowing
- [ ] Billing alarm set
- [ ] BUG-006 status noted in release notes (workaround or fix)
- [ ] `.env` has not been committed — confirmed by git history check
