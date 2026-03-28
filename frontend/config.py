"""
Configurações do Front-End Cálculão

Todas as URLs base dos serviços remotos e variáveis sensíveis são lidas de
variáveis de ambiente, com fallback para valores padrão de desenvolvimento.

Serviços hospedados no Render:
  • Frontend:  https://openroute-frontend.onrender.com
  • Backend:   https://openroute-backend.onrender.com   (BACKEND_URL)
  • API GLP:   https://gas-prices-api-project.onrender.com  (GAS_API_URL)
"""

import os

# ---------------------------------------------------------------------------
# OpenRouteService API Key
# ---------------------------------------------------------------------------
# Produção (Render): definida como variável de ambiente ORS_API_KEY
# Desenvolvimento local: valor hardcoded abaixo (não versionar em projetos reais)
ORS_API_KEY = os.environ.get(
    "ORS_API_KEY",
    "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjVmYWRhYTFlZmQwZjRmMmNiODJkYmMxZWQ1MWE2OWIwIiwiaCI6Im11cm11cjY0In0="
)

# ---------------------------------------------------------------------------
# URL base do back-end de rotas
# ---------------------------------------------------------------------------
# Produção (Render): variável de ambiente BACKEND_URL aponta para o serviço
#   openroute-backend (ex: https://openroute-backend.onrender.com)
# Desenvolvimento local: localhost:8000
_raw_backend = os.environ.get("BACKEND_URL", "http://localhost:8000")

# O Render injeta os hostnames dos fromService sem o esquema — garantimos https://
if _raw_backend.startswith("http://") or _raw_backend.startswith("https://"):
    BACKEND_URL = _raw_backend
else:
    BACKEND_URL = f"https://{_raw_backend}"

# ---------------------------------------------------------------------------
# URL base da API de preços de combustível (ANP)
# ---------------------------------------------------------------------------
# Produção (Render): variável de ambiente GAS_API_URL
# Desenvolvimento local / fallback: serviço público no Render
GAS_API_URL = os.environ.get(
    "GAS_API_URL",
    "https://gas-prices-api-project.onrender.com"
)

# ---------------------------------------------------------------------------
# Parâmetros de warm-up (cold start no Render free tier)
# ---------------------------------------------------------------------------
# Tempo máximo (segundos) que cada thread de wake-up aguarda o serviço subir
WAKEUP_MAX_WAIT = int(os.environ.get("WAKEUP_MAX_WAIT", "180"))
# Intervalo (segundos) entre tentativas de wake-up
WAKEUP_POLL_INTERVAL = int(os.environ.get("WAKEUP_POLL_INTERVAL", "5"))

# ---------------------------------------------------------------------------
# Timeouts gerais (em segundos)
# ---------------------------------------------------------------------------
GEOCODING_TIMEOUT = 10
# Render free tier: cold start (~60s) + Overpass API query (~180s) = 240s de margem
ROUTING_TIMEOUT = 240

# ---------------------------------------------------------------------------
# Configurações do mapa
# ---------------------------------------------------------------------------
DEFAULT_ZOOM = 13
MAP_WIDTH = 1200
MAP_HEIGHT = 600
