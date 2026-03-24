"""
Serviço de preços e custos de combustível

Integra com a API de preços ANP (gas-prices-api-project.onrender.com) para:
- Buscar preço do combustível selecionado pelo usuário no estado de origem
- Buscar preço do GNV no mesmo estado
- Calcular e comparar custos estimados para a rota calculada
"""

import requests
import logging
import time
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL base da API de preços ANP
# ---------------------------------------------------------------------------
GAS_PRICES_API_URL = "https://gas-prices-api-project.onrender.com"

# ---------------------------------------------------------------------------
# Mapeamento: nome completo do estado → sigla UF
# Inclui variações de grafia para máxima robustez
# ---------------------------------------------------------------------------
ESTADO_PARA_UF: Dict[str, str] = {
    # Nomes canônicos
    "Acre": "AC",
    "Alagoas": "AL",
    "Amapá": "AP",
    "Amazonas": "AM",
    "Bahia": "BA",
    "Ceará": "CE",
    "Distrito Federal": "DF",
    "Espírito Santo": "ES",
    "Goiás": "GO",
    "Maranhão": "MA",
    "Mato Grosso": "MT",
    "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG",
    "Pará": "PA",
    "Paraíba": "PB",
    "Paraná": "PR",
    "Pernambuco": "PE",
    "Piauí": "PI",
    "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS",
    "Rondônia": "RO",
    "Roraima": "RR",
    "Santa Catarina": "SC",
    "São Paulo": "SP",
    "Sergipe": "SE",
    "Tocantins": "TO",
    # Variações sem acento (comuns em respostas de geocoder)
    "Amapa": "AP",
    "Ceara": "CE",
    "Espirito Santo": "ES",
    "Goias": "GO",
    "Maranhao": "MA",
    "Mato Grosso do Norte": "RN",  # proteção extra
    "Para": "PA",
    "Paraiba": "PB",
    "Parana": "PR",
    "Piaui": "PI",
    "Rio Grande do Norte": "RN",
    "Rondonia": "RO",
    "Sao Paulo": "SP",
    # Siglas já no formato correto (passadas diretamente)
    "AC": "AC", "AL": "AL", "AP": "AP", "AM": "AM",
    "BA": "BA", "CE": "CE", "DF": "DF", "ES": "ES",
    "GO": "GO", "MA": "MA", "MT": "MT", "MS": "MS",
    "MG": "MG", "PA": "PA", "PB": "PB", "PR": "PR",
    "PE": "PE", "PI": "PI", "RJ": "RJ", "RN": "RN",
    "RS": "RS", "RO": "RO", "RR": "RR", "SC": "SC",
    "SP": "SP", "SE": "SE", "TO": "TO",
}

# ---------------------------------------------------------------------------
# Mapeamento: chave do front-end → nome canônico da API + sigla interna
# ---------------------------------------------------------------------------
FUEL_MAP: Dict[str, Dict[str, str]] = {
    "gasolina_comum":     {"api_name": "gasolina comum",    "sigla": "GC",  "label": "Gasolina Comum",    "unidade": "l"},
    "gasolina_aditivada": {"api_name": "gasolina aditivada","sigla": "GA",  "label": "Gasolina Aditivada","unidade": "l"},
    "diesel_comum":       {"api_name": "diesel",            "sigla": "DC",  "label": "Diesel Comum",      "unidade": "l"},
    "diesel_s10":         {"api_name": "diesel s10",        "sigla": "DS10","label": "Diesel S10",        "unidade": "l"},
    "alcool":             {"api_name": "etanol",            "sigla": "A",   "label": "Álcool (Etanol)",   "unidade": "l"},
}

# Entrada separada para GNV (não aparece no seletor de usuário, mas é sempre calculado)
GNV_API_NAME = "gnv"
GNV_SIGLA = "GNV"
GNV_LABEL = "GNV"
GNV_UNIDADE = "m³"

# ---------------------------------------------------------------------------
# Consumo médio (km por litro ou m³) — média aritmética das faixas definidas
# ---------------------------------------------------------------------------
CONSUMO_MEDIO: Dict[str, float] = {
    "GC":   3.5,   # Gasolina comum:    (2+5)/2
    "GA":   3.5,   # Gasolina aditivada:(2+5)/2
    "DC":   2.5,   # Diesel comum:      (2+3)/2
    "DS10": 3.25,  # Diesel S10:        (2.5+4)/2
    "GNV":  2.5,   # GNV:               (2+3)/2
    "A":    1.0,   # Álcool (etanol):   1 km/l (valor fixo)
}


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def health_check(timeout: int = 8) -> Tuple[bool, str]:
    """
    Verifica se a API de preços ANP está disponível.

    Returns:
        (True, "") se respondeu OK.
        (False, motivo) em caso de falha.
    """
    try:
        response = requests.get(f"{GAS_PRICES_API_URL}/combustiveis", timeout=timeout)
        if response.status_code == 200:
            return True, ""
        return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError as e:
        return False, f"Conexão recusada / URL inválida: {e}"
    except requests.exceptions.Timeout:
        return False, "Timeout (servidor ainda inicializando)"
    except Exception as e:  # pylint: disable=broad-except
        return False, f"Erro inesperado: {e}"


def wake_up(max_wait_seconds: int = 180, poll_interval: int = 5) -> Tuple[bool, str]:
    """
    Acorda a API de preços ANP no Render (cold start), aguardando até
    max_wait_seconds antes de desistir.

    Args:
        max_wait_seconds: Tempo máximo de espera em segundos (default: 180s).
        poll_interval:    Intervalo entre tentativas em segundos (default: 5s).

    Returns:
        (True, "") se o servidor acordou.
        (False, último_motivo) se o tempo esgotou.
    """
    elapsed = 0
    last_detail = "Nenhuma tentativa realizada"
    while elapsed < max_wait_seconds:
        ok, detail = health_check(timeout=poll_interval)
        if ok:
            return True, ""
        last_detail = detail
        time.sleep(poll_interval)
        elapsed += poll_interval
    return False, last_detail

def normalize_state_to_uf(state_text: Optional[str]) -> Optional[str]:
    """
    Converte qualquer representação de estado para a sigla UF de 2 letras.

    Args:
        state_text: Nome completo, sigla, ou variação sem acento do estado

    Returns:
        Sigla UF em maiúsculas (ex: 'RN') ou None se não reconhecido
    """
    if not state_text:
        return None

    text = state_text.strip()

    # Tentativa 1: busca exata no mapeamento
    result = ESTADO_PARA_UF.get(text)
    if result:
        return result

    # Tentativa 2: uppercase (trata siglas em minúscula como 'rn')
    result = ESTADO_PARA_UF.get(text.upper())
    if result:
        return result

    # Tentativa 3: title-case (trata "rio grande do norte" → "Rio Grande Do Norte")
    result = ESTADO_PARA_UF.get(text.title())
    if result:
        return result

    # Tentativa 4: busca parcial case-insensitive (último recurso)
    text_lower = text.lower()
    for key, uf in ESTADO_PARA_UF.items():
        if key.lower() == text_lower:
            return uf

    logger.warning("Estado não reconhecido: '%s'", state_text)
    return None


def get_fuel_label(fuel_key: str) -> str:
    """Retorna o label amigável do combustível selecionado."""
    return FUEL_MAP.get(fuel_key, {}).get("label", fuel_key)


def get_fuel_unit(fuel_key: str) -> str:
    """Retorna a unidade do combustível selecionado (l ou m³)."""
    return FUEL_MAP.get(fuel_key, {}).get("unidade", "l")


def get_consumption_rate(sigla: str) -> Optional[float]:
    """
    Retorna o consumo médio (km/l ou km/m³) para a sigla interna.

    Args:
        sigla: Sigla interna (GC, GA, DC, DS10, GNV, A)

    Returns:
        Consumo médio como float, ou None se não encontrado
    """
    return CONSUMO_MEDIO.get(sigla)


def get_fuel_price(estado_uf: str, api_fuel_name: str, timeout: int = 10) -> Optional[float]:
    """
    Consulta o preço médio de um combustível em um estado na API ANP.

    Args:
        estado_uf:     Sigla do estado (ex: 'RN')
        api_fuel_name: Nome canônico do combustível aceito pela API (ex: 'gasolina comum')
        timeout:       Timeout em segundos para a requisição

    Returns:
        Preço médio em R$ (float) ou None em caso de falha
    """
    try:
        url = f"{GAS_PRICES_API_URL}/preco"
        params = {"estado": estado_uf.upper(), "combustivel": api_fuel_name}

        logger.info("Consultando preço: %s em %s", api_fuel_name, estado_uf)
        response = requests.get(url, params=params, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            price = data.get("preco_medio")
            if price is not None:
                logger.info("Preço obtido: R$ %.4f para %s/%s", price, api_fuel_name, estado_uf)
                return float(price)
            logger.warning("Campo 'preco_medio' ausente na resposta.")
            return None

        elif response.status_code == 404:
            logger.warning(
                "Preço não encontrado (404) para %s em %s. Detalhe: %s",
                api_fuel_name, estado_uf, response.text
            )
            return None

        elif response.status_code == 503:
            logger.warning("API de preços indisponível (503 — dados ainda carregando).")
            return None

        else:
            logger.warning("Resposta inesperada da API de preços: %d", response.status_code)
            return None

    except requests.exceptions.Timeout:
        logger.warning("Timeout ao consultar API de preços (%s / %s).", api_fuel_name, estado_uf)
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("Falha de conexão com API de preços.")
        return None
    except (ValueError, KeyError, TypeError) as exc:
        logger.warning("Resposta malformada da API de preços: %s", exc)
        return None
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Erro inesperado ao consultar API de preços: %s", exc)
        return None


def calculate_fuel_cost(distance_km: float, sigla: str, price_per_unit: float) -> Optional[float]:
    """
    Calcula o custo total de combustível para uma rota.

    Fórmula: (distancia_km / consumo_medio) * preco_por_unidade

    Args:
        distance_km:    Distância em km
        sigla:          Sigla interna do combustível
        price_per_unit: Preço do combustível em R$/l ou R$/m³

    Returns:
        Custo total em R$ ou None se consumo não disponível
    """
    consumo = CONSUMO_MEDIO.get(sigla)
    if consumo is None or consumo == 0:
        logger.warning("Consumo médio não encontrado para sigla '%s'.", sigla)
        return None

    if price_per_unit <= 0:
        return None

    quantidade = distance_km / consumo
    return quantidade * price_per_unit


def build_cost_comparison(
    distance_km: float,
    fuel_key: str,
    estado_uf: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Orquestra a busca de preços e o cálculo comparativo de custos.

    Args:
        distance_km: Distância da rota em km
        fuel_key:    Chave do combustível selecionado (ex: 'gasolina_comum')
        estado_uf:   Sigla do estado do ponto A (ex: 'RN')

    Returns:
        Dicionário com todos os campos para exibição, ou None se dados insuficientes
    """
    if not estado_uf:
        logger.warning("Estado não identificado — cálculo de custo ignorado.")
        return None

    fuel_info = FUEL_MAP.get(fuel_key)
    if not fuel_info:
        logger.warning("Combustível desconhecido: '%s'.", fuel_key)
        return None

    sigla_sel = fuel_info["sigla"]
    api_name_sel = fuel_info["api_name"]
    label_sel = fuel_info["label"]
    unidade_sel = fuel_info["unidade"]

    # Busca preços (paralelismo não necessário — ambas as chamadas são rápidas)
    preco_sel = get_fuel_price(estado_uf, api_name_sel)
    preco_gnv = get_fuel_price(estado_uf, GNV_API_NAME)

    consumo_sel = CONSUMO_MEDIO.get(sigla_sel)
    consumo_gnv = CONSUMO_MEDIO.get(GNV_SIGLA)

    # Calcula quantidades consumidas
    qtd_sel = (distance_km / consumo_sel) if (consumo_sel and consumo_sel > 0) else None
    qtd_gnv = (distance_km / consumo_gnv) if (consumo_gnv and consumo_gnv > 0) else None

    # Calcula custos
    custo_sel = None
    if preco_sel is not None and qtd_sel is not None:
        custo_sel = qtd_sel * preco_sel

    custo_gnv = None
    if preco_gnv is not None and qtd_gnv is not None:
        custo_gnv = qtd_gnv * preco_gnv

    # Percentual de economia com GNV
    economia_pct: Optional[float] = None
    if custo_sel and custo_gnv and custo_sel > 0:
        economia_pct = ((custo_sel - custo_gnv) / custo_sel) * 100

    return {
        "estado_uf":       estado_uf,
        # Combustível selecionado
        "fuel_key":        fuel_key,
        "fuel_label":      label_sel,
        "fuel_api_name":   api_name_sel,
        "fuel_sigla":      sigla_sel,
        "fuel_unidade":    unidade_sel,
        "preco_sel":       preco_sel,
        "consumo_sel":     consumo_sel,
        "qtd_sel":         qtd_sel,
        "custo_sel":       custo_sel,
        # GNV
        "preco_gnv":       preco_gnv,
        "consumo_gnv":     consumo_gnv,
        "qtd_gnv":         qtd_gnv,
        "custo_gnv":       custo_gnv,
        # Meta
        "distance_km":     distance_km,
        "economia_pct":    economia_pct,
    }
