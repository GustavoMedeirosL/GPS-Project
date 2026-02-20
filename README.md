# OpenRoute Navigator - MVP

Multi-criteria routing system using OpenStreetMap data via Overpass API.

## 🎯 Objetivo

Backend Python que calcula rotas alternativas entre origem e destino, considerando diferentes critérios de otimização:
- **Mais Rápida**: Menor distância total
- **Melhor Qualidade**: Prioriza asfalto e bom estado de conservação
- **Mais Segura**: Prioriza vias iluminadas com sinalização
- **Compatível com Caminhões**: Exclui vias com restrições de altura/peso

## 🏗️ Arquitetura

```
GPS2/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   └── routes.py           # API endpoints
│   ├── services/
│   │   ├── geocoding.py        # Nominatim integration
│   │   ├── overpass.py         # Overpass API + graph building
│   │   ├── routing.py          # Multi-criteria pathfinding
│   │   └── scoring.py          # Edge weights + alerts
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   └── utils/
│       └── osm_weights.py      # Weight configurations
├── requirements.txt
└── README.md
```

## 🚀 Instalação

### 1. Criar ambiente virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Instalar dependências

```powershell
pip install -r requirements.txt
```

### 3. Executar servidor

```powershell
uvicorn app.main:app --reload
```

O servidor estará disponível em: `http://localhost:8000`

## 📚 Documentação da API

Após iniciar o servidor, acesse:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints

### POST `/route/calculate`

Calcula rotas entre origem e destino.

**Request Body:**

```json
{
  "origin": "Natal, RN, Brazil",
  "destination": "Ponta Negra, Natal, RN",
  "vehicle": {
    "vehicle_type": "truck",
    "height": 4.2,
    "weight": 28
  }
}
```

Ou usando coordenadas:

```json
{
  "origin": {
    "lat": -5.7945,
    "lon": -35.2110
  },
  "destination": {
    "lat": -5.8822,
    "lon": -35.1767
  },
  "vehicle": {
    "vehicle_type": "car"
  }
}
```

**Response:**

```json
{
  "routes": [
    {
      "type": "fastest",
      "distance_km": 12.4,
      "geometry": [
        [-35.2110, -5.7945],
        [-35.2115, -5.7950],
        ...
      ],
      "alerts": [
        {
          "level": "yellow",
          "message": "No street lighting",
          "location": {
            "lat": -5.8000,
            "lon": -35.2000
          }
        }
      ],
      "summary": "2 caution(s)"
    },
    {
      "type": "best_surface",
      "distance_km": 13.1,
      "geometry": [...],
      "alerts": [],
      "summary": "Route is clear with no warnings"
    },
    {
      "type": "safest",
      "distance_km": 14.2,
      "geometry": [...],
      "alerts": [],
      "summary": "Route is clear with no warnings"
    },
    {
      "type": "truck_compatible",
      "distance_km": 15.0,
      "geometry": [...],
      "alerts": [
        {
          "level": "red",
          "message": "Height restriction: 4.0m (vehicle: 4.2m)",
          "location": {
            "lat": -5.8500,
            "lon": -35.1900
          }
        }
      ],
      "summary": "1 critical alert(s)"
    }
  ],
  "origin_coords": {
    "lat": -5.7945,
    "lon": -35.2110
  },
  "destination_coords": {
    "lat": -5.8822,
    "lon": -35.1767
  }
}
```

### GET `/health`

Health check do serviço.

## 🎨 Critérios de Roteamento

### 1. Fastest (Mais Rápida)
- **Objetivo**: Minimizar distância total
- **Pesos**:
  - Distância: 1.0x
  - Tipo de via: 0.5x
  - Superfície: 0.1x
  - Segurança: 0.0x

### 2. Best Surface (Melhor Qualidade)
- **Objetivo**: Priorizar vias pavimentadas
- **Pesos**:
  - Distância: 1.0x
  - Tipo de via: 0.3x
  - Superfície: 2.0x
  - Qualidade: 2.0x
  - Segurança: 0.1x
- **Prioriza**:
  - `surface=asphalt`
  - `smoothness=good|excellent`
- **Penaliza**:
  - `surface=unpaved|dirt|gravel`
  - `smoothness=bad|very_bad`

### 3. Safest (Mais Segura)
- **Objetivo**: Maximizar segurança viária
- **Pesos**:
  - Distância: 1.0x
  - Tipo de via: 0.5x
  - Superfície: 0.5x
  - Segurança: 3.0x
- **Prioriza**:
  - `lit=yes` (vias iluminadas)
  - `traffic_signals=yes`
- **Penaliza**:
  - `maxspeed > 80`
  - Ausência de iluminação

### 4. Truck Compatible (Compatível com Caminhões)
- **Objetivo**: Respeitar restrições de caminhões
- **Exclui automaticamente**:
  - `maxheight < altura_veículo`
  - `maxweight < peso_veículo`
  - `hgv=no`
  - `access=private|no`
- **Pesos**:
  - Distância: 1.0x
  - Tipo de via: 1.0x
  - Superfície: 1.5x
  - Qualidade: 1.0x
  - Segurança: 0.5x

## 🚨 Sistema de Alertas

### 🟢 Verde (Green)
Via adequada, sem restrições ou problemas.

### 🟡 Amarelo (Yellow)
Atenção necessária:
- Via sem iluminação
- Superfície não pavimentada
- Qualidade ruim (`smoothness=bad`)
- Alta velocidade (`maxspeed > 100`)
- Folga pequena para altura/peso
- Acesso limitado (`access=destination`)

### 🔴 Vermelho (Red)
Restrição crítica:
- Altura insuficiente (`maxheight < veículo`)
- Peso excedido (`maxweight < veículo`)
- Caminhões proibidos (`hgv=no`)
- Acesso privado (`access=private|no`)
- Superfície muito ruim (`surface=mud`)

## 🗺️ Tags OSM Utilizadas

O sistema consulta as seguintes tags do OpenStreetMap:

| Tag | Descrição | Uso |
|-----|-----------|-----|
| `highway` | Tipo de via | Classificação da estrada |
| `surface` | Tipo de superfície | Qualidade do pavimento |
| `smoothness` | Qualidade da via | Estado de conservação |
| `tracktype` | Tipo de trilha | Para vias não pavimentadas |
| `lit` | Iluminação | Segurança noturna |
| `traffic_signals` | Sinalização | Segurança viária |
| `maxspeed` | Velocidade máxima | Segurança |
| `maxheight` | Altura máxima | Restrição para caminhões |
| `maxweight` | Peso máximo | Restrição para caminhões |
| `hgv` | Heavy Goods Vehicle | Permissão para caminhões |
| `access` | Tipo de acesso | Restrições gerais |

## 🧪 Testes

### Teste Manual via cURL

```powershell
curl -X POST "http://localhost:8000/route/calculate" `
  -H "Content-Type: application/json" `
  -d '{
    "origin": {"lat": -5.7945, "lon": -35.2110},
    "destination": {"lat": -5.8822, "lon": -35.1767},
    "vehicle": {"vehicle_type": "car"}
  }'
```

### Teste com Endereços

```powershell
curl -X POST "http://localhost:8000/route/calculate" `
  -H "Content-Type: application/json" `
  -d '{
    "origin": "UFRN, Natal, RN",
    "destination": "Ponta Negra, Natal, RN",
    "vehicle": {
      "vehicle_type": "truck",
      "height": 4.2,
      "weight": 28
    }
  }'
```

## 📊 Exemplo de Query Overpass

A aplicação utiliza queries Overpass QL como esta:

```overpass
[out:json][timeout:60];
(
  way["highway"]
      ["highway"!="footway"]
      ["highway"!="path"]
      ["highway"!="steps"]
      ["highway"!="cycleway"]
      ["highway"!="bridleway"]
      ["highway"!="construction"]
      ["highway"!="proposed"]
      (-5.9,-35.3,-5.7,-35.1);
);
out body;
>;
out skel qt;
```

## ⚙️ Configurações

Os pesos e fatores de penalização podem ser ajustados em:
- `app/utils/osm_weights.py`

Principais configurações:
- `HIGHWAY_WEIGHTS`: Pesos por tipo de via
- `SURFACE_WEIGHTS`: Pesos por tipo de superfície
- `SMOOTHNESS_WEIGHTS`: Pesos por qualidade
- `SAFETY_FACTORS`: Fatores de segurança
- `CRITERIA_MULTIPLIERS`: Multiplicadores por critério

## 🔧 Troubleshooting

### Overpass API Timeout
Se receber erro de timeout:
- Reduza a área de busca (origem e destino mais próximos)
- Ajuste o padding em `overpass.py` (padrão: 0.05°)

### Sem Rotas Encontradas
- Verifique se origem e destino estão em áreas com vias mapeadas no OSM
- Para caminhões, use áreas menos restritivas
- Teste com coordenadas próximas a vias principais

### Geocoding Falhou
- Verifique conectividade com Nominatim
- Use coordenadas diretas em vez de endereços
- Seja mais específico no endereço (cidade, estado, país)

## 📝 Licença

MIT License

## 🤝 Contribuindo

Este é um MVP. Contribuições são bem-vindas para:
- Otimização de performance
- Novos critérios de roteamento
- Cache de resultados
- Testes unitários
- Documentação adicional

## 📧 Contato

OpenRoute Navigator Team - contact@openroutenav.com
