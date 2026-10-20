# AeroGuard 2.1 — Containerized Deployment & Operations Guide

This guide details the containerized architecture, networking model, and commands for building, running, and managing AeroGuard 2.1 using Docker Compose.

---

## 1. Architecture & Port Mapping

```
                       User Browser (Host Machine)
                       /                        \
          :3000 (UI)  /                          \  :8000 (API)
                     v                            v
          +-----------------------+      +-----------------------+
          |   aeroguard-frontend  |      |   aeroguard-backend   |
          |     (Nuxt 4 / SSR)    |----->|  (FastAPI / Scikit)   |
          |       Port 3000       |      |       Port 8000       |
          +-----------------------+      +-----------------------+
                     \                              /
                      +--- [aeroguard-network] ----+
```

- **Frontend (`aeroguard-frontend`):** Listens on container port 3000, mapped to host `http://localhost:3000`.
- **Backend (`aeroguard-backend`):** Listens on container port 8000, mapped to host `http://localhost:8000`.
- **Health Synchronization:** The frontend waits for `aeroguard-backend` to pass its health check (`/api/health`) before starting.

---

## 2. Docker Compose Commands

### Build Containers
```bash
docker compose build
```

### Start Services in Background
```bash
docker compose up -d
```

### Check Service Status & Health
```bash
docker compose ps
```
Both containers will report `(healthy)` when operational.

### Stream Service Logs
```bash
# View combined logs
docker compose logs -f

# View backend only
docker compose logs -f backend

# View frontend only
docker compose logs -f frontend
```

### Stop Services
```bash
docker compose down
```

---

## 3. Local Development (Bare-Metal Fallback)

If Docker is unavailable, AeroGuard 2.1 retains full bare-metal execution support:

### Terminal 1 — FastAPI Backend:
```powershell
$env:PYTHONPATH="src"
.venv\Scripts\python -m uvicorn aircraft_pm.api:app --host 127.0.0.1 --port 8000
```

### Terminal 2 — Nuxt 4 Frontend:
```powershell
cd frontend
bun run dev
```

### Terminal 3 — Streamlit Operations Suite:
```powershell
$env:PYTHONPATH="src"
.venv\Scripts\streamlit run src/aircraft_pm/app.py --server.port 8501
```
