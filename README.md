Weather Ingestor API
API simples para buscar dados horários de temperatura da Open-Meteo API , armazenar em SQLite e expor endpoints com previsão média por cidade.

✨ Funcionalidades
Ingestão de dados climáticos horários
Armazenamento em SQLite
Filtragem por cidade e data
Endpoint /sync-weather : Busca e salva dados de temperatura
Endpoint /week : Retorna a média diurna (6h–18h) para os próximos 7 dias
Endpoint /locations : Lista todas as cidades sincronizadas
Suporte a múltiplas localizações (ex: Berlim, São Paulo, Londres...)
uvicorn app.main:app --reload

Como Rodar
Pré-requisitos:
Docker
Docker Compose
Passo a passo:

# Clonar repositório
git clone https://github.com/seu-usuario/weather-ingestor.git 
cd weather-ingestor

# Subir serviço
docker-compose up --build

Acesse a documentação automática:
http://localhost:8000/docs

Endpoints
POST /sync-weather
Busca dados da Open-Meteo e salva no banco local.

Parâmetros:
latitude: Latitude da cidade (padrão: 52.52)
longitude: Longitude da cidade (padrão: 13.41)

Exemplo:
curl -X POST "http://localhost:8000/sync-weather?latitude=-23.55&longitude=-46.63"

Resposta:
{
  "rows_upserted": 24,
  "city": "Sao Paulo"
}

GET /week
Retorna a média da temperatura durante o dia (6h–18h) para cada dia da próxima semana.

Parâmetros:
latitude: Latitude da cidade (padrão: 52.52)
longitude: Longitude da cidade (padrão: 13.41)

Exemplo:
curl "http://localhost:8000/week?latitude=-23.55&longitude=-46.63"

Resposta:

{
  "Sao Paulo": {
    "2025-04-07": 14.5,
    "2025-04-08": 13.9
  }
}

GET /locations
Lista todas as cidades cujos dados já foram sincronizados.

Exemplo:
curl "http://localhost:8000/locations"

Resposta:
{
  "locations": ["Berlin", "Sao Paulo", "London"]
}

GET /weather
Lista as últimas N temperaturas armazenadas.

Parâmetro opcional:
limit: Quantidade de registros (padrão: 10)

Exemplo:
curl "http://localhost:8000/weather?limit=5"

Resposta:

[
  {"timestamp": "2025-04-07T14:00", "temperature": 14.5, "city": "Berlin"},
  ...
]

Estrutura do Projeto

.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── app/
    ├── main.py
    ├── models.py
    ├── database.py
    ├── schema.py
    └── config.py


