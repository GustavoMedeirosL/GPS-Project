# Cálculão - Guia do Front-End

## 🚀 Início Rápido

### 1. Instalar Dependências

```powershell
pip install -r requirements.txt
```

### 2. Iniciar o Back-End (em um terminal)

```powershell
uvicorn app.main:app --reload
```

### 3. Iniciar o Front-End (em outro terminal)

```powershell
cd frontend
streamlit run app.py
```

O front-end estará disponível em: **http://localhost:8501**

---

## 📁 Estrutura do Front-End

```
frontend/
├── app.py                      # Aplicação principal Streamlit
├── services/
│   ├── __init__.py
│   ├── ors_geocoding.py       # Serviço de geocodificação (com extração de estado)
│   ├── backend_client.py      # Cliente da API back-end
│   └── fuel_service.py        # Estimativa de custo com combustível e GNV
├── ui/
│   ├── __init__.py
│   └── layout.py              # Componentes de interface
└── utils/
    ├── __init__.py
    └── map_utils.py           # Utilitários para mapas Folium
```

---

## 🎯 Funcionalidades

### Geocodificação Automática
- Converte endereços de texto em coordenadas
- Usa API do OpenRouteService
- Tratamento robusto de erros

### Cálculo de Rotas
- Comunica com back-end FastAPI
- Suporta múltiplos critérios:
  - 🚗 Mais Rápida
  - 🛣️ Melhor Pavimento
  - 🛡️ Mais Segura
  - 🚛 Compatível com Caminhão (com altura e peso)

### Estimativa de Custo com Combustível
- Detecta automaticamente o **estado** de origem via geocodificação
- Consulta preços reais da **ANP** (Agência Nacional de Petróleo)
- Suporta: Gasolina Comum, Gasolina Aditivada, Diesel Comum, Diesel S10, Álcool (Etanol)
- Calcula a **quantidade estimada** e o **custo total** da rota
- Compara com o custo usando **GNV** (Gás Natural Veicular)
- Exibe a **economia percentual** ao usar GNV quando disponível

### Visualização Interativa
- Mapas Folium integrados
- Marcadores de origem e destino
- Linhas de rota coloridas por critério
- Alertas visualizados no mapa
- Popups informativos

### Interface Intuitiva
- Formulário simples e direto
- Feedback visual durante processamento
- Mensagens claras de erro
- Comparação de rotas e custo de combustível

---

## 🔧 Configuração

### API do OpenRouteService

O geocoding usa a API pública do OpenRouteService (sem necessidade de chave).

Para uso intensivo, obtenha uma chave gratuita em: https://openrouteservice.org/

Edite `frontend/services/ors_geocoding.py`:

```python
geocoding_service = ORSGeocodingService(api_key="SUA_CHAVE_AQUI")
```

### URL do Back-End

Por padrão: `http://localhost:8000`

Para alterar, edite `frontend/services/backend_client.py`:

```python
backend_client = BackendClient(base_url="http://seu-servidor:porta")
```

---

## 📖 Como Usar

1. **Digite a origem e destino** (endereços completos)
   - Exemplo: "UFRN, Natal, RN"
   - Exemplo: "Ponta Negra, Natal, RN"

2. **Selecione o combustível** do seu veículo
   - ⛽ Gasolina Comum
   - ⛽ Gasolina Aditivada
   - 🚛 Diesel Comum
   - 🚛 Diesel S10
   - 🌿 Álcool (Etanol)

3. **Selecione o critério de rota**
   - 🚗 Mais Rápida
   - 🛣️ Melhor Pavimento
   - 🛡️ Mais Segura
   - 🚛 Compatível com Caminhão

4. **Para caminhões**, informe:
   - Altura (metros)
   - Peso (toneladas)

5. **Clique em "Calcular Rota"**

6. **Visualize o resultado**:
   - Resumo da rota selecionada
   - Alertas e avisos no trajeto
   - Mapa interativo com todas as rotas
   - Comparação entre critérios
   - **Estimativa de custo** com o combustível escolhido
   - **Comparação com GNV** e economia percentual

---

## ⚠️ Troubleshooting

### Front-end não inicia

```powershell
# Verificar se Streamlit foi instalado
pip install streamlit

# Executar do diretório correto
cd frontend
streamlit run app.py
```

### "Back-end não disponível"

Verifique se o back-end está rodando:

```powershell
# Em outro terminal
uvicorn app.main:app --reload
```

Acesse http://localhost:8000/docs para verificar.

### Erro de geocodificação

- Verifique sua conexão com a internet
- Use endereços mais específicos
- Inclua cidade e estado

### Mapa não aparece

```powershell
# Reinstalar dependências de mapa
pip install folium streamlit-folium --upgrade
```

---

## 🎨 Personalização

### Cores das Rotas

Edite `frontend/utils/map_utils.py`:

```python
ROUTE_COLORS = {
    'fastest': '#2E7D32',        # Verde
    'best_surface': '#1976D2',   # Azul
    'safest': '#00897B',         # Teal
    'truck_compatible': '#F57C00' # Laranja
}
```

### Layout da Interface

Edite `frontend/ui/layout.py` para customizar:
- Títulos e descrições
- Mensagens de erro
- Formato das métricas
- Estilo dos componentes

---

## 🧪 Exemplos de Uso

### Exemplo 1: Rota rápida com estimativa de custo

**Origem:** UFRN, Natal, RN  
**Destino:** Ponta Negra, Natal, RN  
**Combustível:** Gasolina Comum  
**Critério:** Mais Rápida  
➡️ O app exibirá o custo estimado em gasolina e a comparação com GNV para o RN.

### Exemplo 2: Rota mais segura com álcool

**Origem:** Shopping Midway Mall, Natal, RN  
**Destino:** Aeroporto de Natal, RN  
**Combustível:** Álcool (Etanol)  
**Critério:** Mais Segura  

### Exemplo 3: Rota para caminhão

**Origem:** Porto de Natal, RN  
**Destino:** Zona Industrial, Natal, RN  
**Combustível:** Diesel S10  
**Critério:** Compatível com Caminhão  
**Altura:** 4.2 m  
**Peso:** 28 ton

---

## 📚 Documentação Técnica

### Módulo: `services/ors_geocoding.py`

**Classe:** `ORSGeocodingService`

```python
# Geocodificar endereço
coords = geocoding_service.geocode("UFRN, Natal, RN")
# Retorna: (latitude, longitude)

# Reverse geocoding
name = geocoding_service.get_location_name(-5.7945, -35.2110)
```

### Módulo: `services/backend_client.py`

**Classe:** `BackendClient`

```python
# Calcular rotas
result = backend_client.calculate_route(
    origin_lat=-5.7945,
    origin_lon=-35.2110,
    dest_lat=-5.8822,
    dest_lon=-35.1767,
    vehicle_type="car"
)

# Obter rota específica
route = backend_client.get_route_by_criteria(
    ...,
    criteria="fastest"
)
```

### Módulo: `utils/map_utils.py`

**Funções principais:**

```python
# Criar mapa com múltiplas rotas
map_obj = create_route_map(
    origin_lat, origin_lon,
    dest_lat, dest_lon,
    routes,
    origin_name="Origem",
    dest_name="Destino"
)

# Criar mapa com rota única
map_obj = create_simple_route_map(...)
```

---

## 🔐 Segurança

- Não exponha chaves de API no código
- Use variáveis de ambiente para configurações sensíveis
- Valide todas as entradas do usuário
- Implemente rate limiting se necessário

---

## 🚀 Próximos Passos

### Melhorias Futuras

1. **Cache de geocoding** para endereços já consultados
2. **Histórico de rotas** salvo localmente
3. **Export de rotas** para GPX/KML
4. **Modo offline** com mapas pré-baixados
5. **Compartilhamento** de rotas via URL
6. **Múltiplos waypoints** (paradas intermediárias)
7. **Estimativa de tempo** de viagem em tempo real
8. **Consumo personalizado** por modelo de veículo
9. **Posto de combustível** mais barato no trajeto

---

**Desenvolvido com ❤️ usando Streamlit + Folium + FastAPI + ANP Fuel Prices API**
