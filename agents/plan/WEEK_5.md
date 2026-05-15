# Week 5 — Docker, Nginx, CI/CD & AWS Deployment

## Goal
`docker-compose up` runs all 5 services cleanly. CI tests and builds on every push. CloudFormation deploys to AWS ECS Fargate. App is live behind an ALB. CloudWatch logs are flowing. Full teardown is documented.

---

## Deliverables

### Docker & Nginx
| File | Description |
|---|---|
| `backend/Dockerfile` | Multi-stage: `python:3.11-slim` → install deps → copy app → uvicorn entrypoint |
| `frontend/Dockerfile` | Stage 1: `node:20-alpine` build (`npm run build`). Stage 2: `nginx:alpine` serve `dist/` |
| `docker-compose.yml` | 5 services: nginx, backend, celery_worker, frontend, redis |
| `docker-compose.prod.yml` | Production overrides: no bind mounts, image tags from ECR |
| `nginx/nginx.conf` | `/api/*` → backend:8000, `/health` → backend:8000, `/*` → frontend:80, gzip + security headers |

### CI/CD
| File | Description |
|---|---|
| `.github/workflows/ci.yml` | 3 jobs: test → build → deploy (deploy is `workflow_dispatch` only) |

### Infrastructure
| File | Description |
|---|---|
| `infra/cloudformation/template.yml` | Full CloudFormation stack (see AWS Architecture below) |
| `infra/cloudformation/parameters.dev.json` | Non-secret parameters (region, cluster name, image tags) |
| `docs/AWS_DEPLOYMENT.md` | Step-by-step deploy and teardown guide |

---

## Docker Compose Services

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    ports: ["80:80"]
    volumes: ["./nginx/nginx.conf:/etc/nginx/nginx.conf:ro"]
    depends_on: [frontend, backend]

  backend:
    build: { context: ./backend }
    env_file: .env
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
    depends_on: [redis]

  celery_worker:
    build: { context: ./backend }
    command: celery -A backend.workers.celery_app worker --loglevel=info --concurrency=2
    env_file: .env
    depends_on: [redis]

  frontend:
    build: { context: ./frontend }
    # Multi-stage: node build → nginx:alpine serve dist/

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes: ["redis_data:/data"]

volumes:
  redis_data:
```

---

## CI Pipeline Jobs

### Job 1: test
- `pytest tests/ -v --tb=short --cov=backend --cov-report=xml`
- `npx tsc --noEmit` (frontend TypeScript check)
- `npm run build` (frontend production build)

### Job 2: build
- `docker build -t nutriplan-backend ./backend`
- `docker build -t nutriplan-frontend ./frontend`

### Job 3: deploy (manual `workflow_dispatch` only — prevents accidental AWS charges)
- OIDC auth to AWS (no long-lived access keys in GitHub secrets)
- Push tagged images to ECR
- `aws cloudformation deploy` with parameter overrides

---

## AWS Architecture

```
Route 53 (optional)
    │
    ▼
ALB (HTTPS, ACM cert)
  ├── /api/* → Backend Target Group (FastAPI, port 8000)
  └── /*     → Frontend Target Group (Nginx, port 80)
    │
    ▼
ECS Fargate Cluster
  ├── Backend Service     (0.5 vCPU / 1 GB)
  ├── Frontend Service    (0.25 vCPU / 512 MB)
  └── Celery Worker      (0.5 vCPU / 1 GB)
    │
External services (no VPC needed):
  Supabase  PostgreSQL + Storage + Auth
  Pinecone  Vector DB
  Redis     AWS ElastiCache Serverless (or Upstash for demo cost)
  OpenAI    HTTPS outbound
  Mistral   HTTPS outbound
    │
    ▼
CloudWatch Log Groups
  /nutriplan/backend · /nutriplan/frontend · /nutriplan/worker
```

---

## CloudFormation Stack Components

| Component | Details |
|---|---|
| ECR Repositories | `nutriplan-backend`, `nutriplan-frontend`, `nutriplan-worker` |
| ECS Cluster | Fargate; Container Insights enabled |
| Task Definitions | Backend: 0.5vCPU/1GB; Frontend: 0.25vCPU/512MB; Worker: 0.5vCPU/1GB |
| ECS Services | `desiredCount=1` each; ALB health-check; 60s grace period |
| IAM Execution Role | ECR pull + CloudWatch write only — no wildcards |
| CloudWatch Log Groups | 7-day retention |
| Security Groups | ALB SG: inbound 80/443; ECS SG: inbound from ALB SG only |
| ALB | HTTP → HTTPS redirect; path-based routing |
| Secrets Manager | `OPENAI_API_KEY`, `MISTRAL_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `PINECONE_API_KEY`, `DATABASE_URL`, `REDIS_URL` |

---

## Cost Controls

- ECS Fargate Spot tasks (up to 70% cheaper)
- CloudWatch billing alarm at $20
- Redis: Upstash free tier during demo (avoids ElastiCache costs)
- **Teardown:** `aws cloudformation delete-stack --stack-name nutriplan-ai`

---

## Acceptance Criteria

- [ ] `docker-compose up` starts all 5 services without errors
- [ ] `http://localhost` serves the frontend; `http://localhost/health` returns 200
- [ ] Full doctor workflow works through Dockerised stack (login → patient → generate → approve)
- [ ] CI: all pytest tests pass + TypeScript check passes + frontend build succeeds on push to `main`
- [ ] CI: all Docker images build without errors
- [ ] `aws cloudformation deploy` creates the stack without errors
- [ ] App accessible via ALB DNS name
- [ ] CloudWatch log streams show structured JSON logs for all three services
- [ ] No API keys in CloudFormation parameters, Docker images, or CI logs (verified by inspection)
- [ ] `docs/AWS_DEPLOYMENT.md` documents full deploy and teardown
- [ ] `PROGRESS.md` marked fully complete

---

## Security Checklist Before Deployment

- [ ] `.env` is in `.gitignore` — verified with `git check-ignore .env`
- [ ] All secrets in AWS Secrets Manager — zero secrets in CloudFormation template or parameters
- [ ] GitHub Actions uses OIDC role assumption — no `AWS_ACCESS_KEY_ID` in GitHub secrets
- [ ] Supabase RLS enabled on all patient tables — verified by integration test
- [ ] Nginx security headers set: `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy`
- [ ] structlog never logs request bodies or patient PII — verified by log inspection
- [ ] Supabase Storage bucket is private — access via signed URLs only
