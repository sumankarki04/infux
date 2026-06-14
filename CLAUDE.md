# INFUX - Agent Instructions (shared by Claude Code + Codex)

INFUX = influencer-brand marketing marketplace. Nepal-first, then global.

## Stack
Flask + Flask-SQLAlchemy + Flask-Login + Flask-Migrate. Supabase (Postgres). gunicorn. Deploy via render.yaml. Run: `python run.py`. Env in .env (see .env.example).

## Layout (app/)
- models/ : user, brand, influencer, campaign, application, message, notification, payment, review
- routes/ : admin, auth, brand, chat, influencer, notifications, payments, public, reviews
- services/, utils/, templates/, static/

## MVP build order
1 Auth (roles admin/brand/influencer) -> 2 Influencer profiles -> 3 Brand profiles -> 4 Campaign posting -> 5 Applications -> 6 Messaging -> 7 Admin dashboard. Then: AI matching, analytics, escrow payments.

## Conventions
- Keep routes thin, logic in services/. Validate input. Never commit secrets (.env is gitignored).
- Small focused commits. Run test_db.py / tests before pushing.

## Working with the OTHER agent
This repo is driven by BOTH Claude Code (reads CLAUDE.md) and OpenAI Codex (reads AGENTS.md) - same content. Conventions above apply to both so output stays consistent. Use feature branches / git worktrees when both run at once; one agent can review the other's diff before merge.