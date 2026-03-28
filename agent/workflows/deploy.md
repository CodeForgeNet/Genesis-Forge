---
description: Production deployment with pre-flight checks and verification.
---

# /deploy — $ARGUMENTS

## Sub-commands
```
/deploy            - Interactive deployment wizard
/deploy check      - Pre-deployment checks only
/deploy preview    - Deploy to staging
/deploy production - Deploy to production
/deploy rollback   - Rollback to previous version
```

## Pre-Deployment
Run checklist from `agent/docs/DEPLOY_CHECKLIST.md` before proceeding.

## Deployment Flow
Pre-flight checks → Build → Deploy to platform → Health check → Complete

## Platform Support
| Platform | Command |
|----------|---------|
| Vercel | `vercel --prod` |
| Railway | `railway up` |
| Fly.io | `fly deploy` |
| Docker | `docker compose up -d` |

## Output Format

**Success:**
```
## 🚀 Deployment Complete
- Version, Environment, Duration, Platform
- URLs: Production + Dashboard
- What Changed
- Health Check results
```

**Failure:**
```
## ❌ Deployment Failed
- Error + Details + Resolution steps
- Rollback: /deploy rollback
```
