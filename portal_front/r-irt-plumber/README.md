# R IRT Plumber (mirt)

Endpoints
- GET /healthz
- POST /irt/calibrate: 2PL unidimensional calibration (small datasets)
- POST /irt/score: Placeholder (501)

Build & Run
```bash
docker build -t r-irt-plumber:dev portal_front/r-irt-plumber
docker run --rm -p 8001:8000 -e PLUMBER_RUN=true r-irt-plumber:dev
```
