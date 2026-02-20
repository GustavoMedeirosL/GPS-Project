# Quick Start Guide - OpenRoute Navigator

## Setup em 3 Passos

### 1️⃣ Instalar Dependências

```powershell
# Navegar para o diretório do projeto
cd "c:\Users\gusta\Documents\UFRN\Projeto de Pesquisa\Another Antigravity Folders\GPS2"

# Instalar as bibliotecas necessárias
pip install fastapi uvicorn pydantic requests networkx shapely geopandas geopy
```

### 2️⃣ Iniciar o Servidor

```powershell
# Executar o servidor FastAPI
uvicorn app.main:app --reload
```

O servidor estará disponível em: **http://localhost:8000**

### 3️⃣ Testar a API

**Opção A: Interface Web (Recomendado)**

Abra no navegador: http://localhost:8000/docs

Clique em "POST /route/calculate" → "Try it out" → Cole este exemplo:

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

**Opção B: Script Python**

Em outro terminal:

```powershell
python test_api.py
```

**Opção C: cURL**

```powershell
curl -X POST "http://localhost:8000/route/calculate" `
  -H "Content-Type: application/json" `
  -d '{
    "origin": {"lat": -5.7945, "lon": -35.2110},
    "destination": {"lat": -5.8822, "lon": -35.1767},
    "vehicle": {"vehicle_type": "car"}
  }'
```

---

## 🎨 Executar o Front-End Streamlit

O projeto inclui um **front-end visual interativo** usando Streamlit + Folium.

**Em um novo terminal (mantendo o back-end rodando):**

```powershell
cd frontend
streamlit run app.py
```

Acesse: **http://localhost:8501**

### Como Usar

1. Digite **origem e destino** (endereços ou coordenadas)
2. Selecione o **critério de rota**
3. Clique em **"Calcular Rota"**
4. Visualize o mapa interativo com a rota

📖 **Documentação completa:** [frontend/README.md](file:///c:/Users/gusta/Documents/UFRN/Projeto%20de%20Pesquisa/Another%20Antigravity%20Folders/GPS2/frontend/README.md)

---

## 🎯 Exemplo de Resposta

```json
{
  "routes": [
    {
      "type": "fastest",
      "distance_km": 12.4,
      "geometry": [[lon, lat], [lon, lat], ...],
      "alerts": [
        {
          "level": "yellow",
          "message": "No street lighting",
          "location": {"lat": -5.8, "lon": -35.2}
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
    }
  ],
  "origin_coords": {"lat": -5.7945, "lon": -35.2110},
  "destination_coords": {"lat": -5.8822, "lon": -35.1767}
}
```

---

## 🚛 Testar com Caminhão

```json
{
  "origin": {"lat": -5.7945, "lon": -35.2110},
  "destination": {"lat": -5.8822, "lon": -35.1767},
  "vehicle": {
    "vehicle_type": "truck",
    "height": 4.2,
    "weight": 28
  }
}
```

Retornará 4 rotas incluindo **"truck_compatible"**!

---

## 🌍 Testar com Endereços

```json
{
  "origin": "UFRN, Natal, RN, Brazil",
  "destination": "Ponta Negra, Natal, RN, Brazil",
  "vehicle": {
    "vehicle_type": "car"
  }
}
```

O sistema fará geocoding automaticamente usando Nominatim.

---

## ⚠️ Troubleshooting

### Erro ao Instalar Dependências

Se `pip install -r requirements.txt` falhar, instale manualmente:

```powershell
pip install fastapi==0.109.0
pip install uvicorn==0.27.0
pip install pydantic==2.5.3
pip install requests==2.31.0
pip install networkx==3.2.1
pip install shapely==2.0.2
pip install geopandas==0.14.2
pip install geopy==2.4.1
```

### Porta 8000 em Uso

Se a porta 8000 já estiver em uso:

```powershell
uvicorn app.main:app --reload --port 8001
```

Então acesse: http://localhost:8001/docs

### Timeout no Overpass API

Se receber timeout, use coordenadas mais próximas ou reduza o bbox padding em `app/services/overpass.py`.

---

## 📚 Documentação Completa

Consulte o [README.md](file:///c:/Users/gusta/Documents/UFRN/Projeto%20de%20Pesquisa/Another%20Antigravity%20Folders/GPS2/README.md) para documentação detalhada.

---

## ✅ Checklist de Teste

- [ ] Servidor iniciou sem erros
- [ ] Acessou http://localhost:8000/docs
- [ ] Testou com coordenadas
- [ ] Recebeu 3 rotas (car) ou 4 rotas (truck)
- [ ] Verificou alertas nas rotas
- [ ] Testou com endereços (geocoding)
- [ ] **Front-end:** Executou `streamlit run app.py`
- [ ] **Front-end:** Testou interface visual interativa

---

**Pronto para usar! 🚀**
