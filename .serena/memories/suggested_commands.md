# Suggested Commands for OpenSNS

## Python / Backend

| Command | Description |
|---------|-------------|
| `cd backend && uvicorn app.main:app --reload` | Start development server |
| `cd backend && pytest` | Run all tests |
| `cd backend && pytest tests/test_specific.py -v` | Run specific test file |
| `cd backend && ruff check app/` | Lint code |
| `cd backend && ruff check --fix app/` | Auto-fix lint issues |
| `cd backend && mypy app/` | Type checking |

## ComfyUI Discovery (New)

| Command | Description |
|---------|-------------|
| `cd backend && python -c "from app.services.comfyui import load_manifest; print(load_manifest('sdxl_background_replace_v1'))"` | Load image workflow manifest |
| `cd backend && python -c "from app.services.comfyui import load_manifest; print(load_manifest('cogvideox_i2v_v1'))"` | Load video workflow manifest |
| `cd backend && pytest tests/test_comfyui_discovery.py -v` | Run ComfyUI discovery tests |

## Frontend

| Command | Description |
|---------|-------------|
| `cd frontend && npm run dev` | Start development server |
| `cd frontend && npm test` | Run tests |
| `cd frontend && npm run build` | Production build |

## Database

| Command | Description |
|---------|-------------|
| `cd backend && alembic revision --autogenerate -m "message"` | Create migration |
| `cd backend && alembic upgrade head` | Run migrations |
| `cd backend && alembic downgrade -1` | Rollback one migration |
