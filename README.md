# Weather Data Ingestor

Uma aplicação FastAPI que busca dados climáticos da API pública Open-Meteo e armazena em SQLite.

## Endpoints

- `POST /sync-weather` → Busca e salva dados horários de temperatura em Berlim
- `GET /week` → Retorna média diária da semana (horário diurno: 6h–18h)
- `GET /weather` → Lista últimos N registros

## Como Rodar

docker-compose up --build

### Localmente (sem Docker):

uvicorn app.main:app --reload

```bash
pip install -r requirements.txt

uvicorn app.main:app --reload