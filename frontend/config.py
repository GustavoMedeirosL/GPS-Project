"""
Configurações do Front-End OpenRoute Navigator

As variáveis sensíveis (API Key, URL do backend) são lidas de variáveis de ambiente,
com fallback para valores locais de desenvolvimento.
"""

import os

# OpenRouteService API Key
# - Produção (Render): definida como variável de ambiente ORS_API_KEY no painel do Render
# - Desenvolvimento local: pode ser definida no ambiente ou deixar o valor hardcoded aqui
ORS_API_KEY = os.environ.get(
    "ORS_API_KEY",
    "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjVmYWRhYTFlZmQwZjRmMmNiODJkYmMxZWQ1MWE2OWIwIiwiaCI6Im11cm11cjY0In0="
)

# URL base do back-end
# - Produção (Render): definida como variável de ambiente BACKEND_URL apontando para
#   o serviço openroute-backend (ex: https://openroute-backend.onrender.com)
# - Desenvolvimento local: localhost:8000
_raw_backend = os.environ.get("BACKEND_URL", "http://localhost:8000")

# O Render injeta apenas o hostname no fromService (sem o https://).
# Garantimos que a URL sempre tenha o esquema correto.
if _raw_backend.startswith("http://") or _raw_backend.startswith("https://"):
    BACKEND_URL = _raw_backend
else:
    BACKEND_URL = f"https://{_raw_backend}"

# Timeouts (em segundos)
GEOCODING_TIMEOUT = 10
# Render free tier: cold start (~60s) + Overpass API query (~180s) = 240s de margem
ROUTING_TIMEOUT = 240

# Configurações do mapa
DEFAULT_ZOOM = 13
MAP_WIDTH = 1200
MAP_HEIGHT = 600
