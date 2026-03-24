"""
OpenRoute Navigator - Front-End Principal
Aplicação Streamlit para visualização de rotas com múltiplos critérios
"""

import streamlit as st
from streamlit_folium import folium_static
import sys
import os

# Adicionar diretório frontend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar configurações
import config

# Importar módulos locais
from services.ors_geocoding import ORSGeocodingService
from services.backend_client import BackendClient
from utils.map_utils import create_route_map, create_simple_route_map
from ui.layout import (
    show_header,
    show_input_form,
    show_loading_with_vehicle,
    show_error,
    show_success,
    show_warning,
    show_info,
    show_route_summary,
    show_all_routes_comparison,
    show_sidebar_info,
    show_footer,
    show_fuel_comparison,
)
from services import fuel_service


# Configuração da página
st.set_page_config(
    page_title="OpenRoute Navigator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_services():
    """
    Inicializa os serviços necessários
    
    Returns:
        Tuple com (geocoding_service, backend_client)
    """
    # Verificar se já existem na sessão
    if 'geocoding_service' not in st.session_state:
        st.session_state.geocoding_service = ORSGeocodingService(api_key=config.ORS_API_KEY)
    
    if 'backend_client' not in st.session_state:
        st.session_state.backend_client = BackendClient(base_url=config.BACKEND_URL)
    
    return st.session_state.geocoding_service, st.session_state.backend_client


def check_backend_status(backend_client: BackendClient, status_placeholder) -> bool:
    """
    Verifica se o back-end está disponível.
    Exibe na sidebar a URL sendo usada e o motivo real de falha.

    Args:
        backend_client:    Cliente do back-end
        status_placeholder: Placeholder da sidebar para atualizar status

    Returns:
        True se disponível (imediato ou após wake-up), False se timeout.
    """
    # Mostra a URL sendo usada – essencial para diagnóstico no Render
    st.sidebar.caption(f"🔗 Backend URL: `{backend_client.base_url}`")

    # Tentativa rápida primeiro (evita spinner desnecessário em dev local)
    ok, detail = backend_client.health_check(timeout=5)
    if ok:
        return True

    # Back-end não respondeu rapidamente — pode ser cold start do Render.
    # Exibe spinner e aguarda até 180 segundos (deploy real leva ~80s).
    status_placeholder.warning("⏳ Aguardando back-end inicializar...")
    with st.spinner(
        "⏳ Aguardando o servidor inicializar (cold start pode levar até 3 min no Render)..."
    ):
        ok, detail = backend_client.wake_up(max_wait_seconds=180, poll_interval=5)

    if not ok:
        # Mostra o motivo real da falha abaixo da URL na sidebar
        st.sidebar.error(f"❌ Detalhe do erro:\n{detail}")

    return ok


def geocode_addresses(geocoding_service, origin: str, destination: str, vehicle_type: str = 'car'):
    """
    Geocodifica origem e destino.
    Para a origem, também extrai o estado (UF) da resposta do geocoder.

    Args:
        geocoding_service: Serviço de geocoding
        origin: Endereço de origem
        destination: Endereço de destino
        vehicle_type: Tipo de veículo ('car', 'motorcycle', 'truck')

    Returns:
        Tuple com ((origin_lat, origin_lon), (dest_lat, dest_lon), estado_uf) ou None se houver erro
    """
    try:
        # Geocodificar origem — usa método extendido para capturar estado
        show_loading_with_vehicle("Localizando origem...", vehicle_type)
        origin_lat, origin_lon, state_raw = geocoding_service.geocode_with_state(origin)
        estado_uf = fuel_service.normalize_state_to_uf(state_raw)
        show_success(f"Origem encontrada: {origin}")

        # Geocodificar destino — método padrão (só precisamos do estado da origem)
        show_loading_with_vehicle("Localizando destino...", vehicle_type)
        dest_coords = geocoding_service.geocode(destination)
        show_success(f"Destino encontrado: {destination}")

        return (origin_lat, origin_lon), dest_coords, estado_uf

    except ValueError as e:
        show_error(f"Erro de geocodificação: {str(e)}")
        return None
    except (ConnectionError, TimeoutError) as e:
        show_error(f"Erro de conexão com serviço de geocoding: {str(e)}")
        return None
    except Exception as e:
        show_error(f"Erro inesperado ao geocodificar: {str(e)}")
        return None


def calculate_routes(backend_client, form_data, origin_coords, dest_coords):
    """
    Calcula rotas usando o back-end
    
    Args:
        backend_client: Cliente do back-end
        form_data: Dados do formulário
        origin_coords: Coordenadas da origem
        dest_coords: Coordenadas do destino
        
    Returns:
        Dict com resultado da API ou None se houver erro
    """
    origin_lat, origin_lon = origin_coords
    dest_lat, dest_lon = dest_coords
    vehicle_type = form_data.get('vehicle_type', 'car')
    
    try:
        show_loading_with_vehicle("Calculando rotas...", vehicle_type)
        result = backend_client.calculate_route(
            origin_lat, origin_lon,
            dest_lat, dest_lon,
            vehicle_type=vehicle_type,
            height=form_data.get('height'),
            weight=form_data.get('weight'),
            timeout=config.ROUTING_TIMEOUT
        )
        
        return result
        
    except ValueError as e:
        show_error(f"Erro de validação: {str(e)}")
        return None
    except ConnectionError as e:
        show_error(f"Erro de conexão com back-end: {str(e)}")
        show_warning("Verifique se o servidor está em execução: uvicorn app.main:app --reload")
        return None
    except TimeoutError as e:
        show_error(f"Timeout ao calcular rotas: {str(e)}")
        show_info("Tente usar coordenadas mais próximas ou aguarde alguns minutos.")
        return None
    except Exception as e:
        show_error(f"Erro inesperado: {str(e)}")
        return None


def find_selected_route(routes, criteria):
    """
    Encontra a rota correspondente ao critério selecionado
    
    Args:
        routes: Lista de rotas
        criteria: Critério selecionado
        
    Returns:
        Rota encontrada ou primeira rota disponível
    """
    for route in routes:
        if route.get('type') == criteria:
            return route
    
    # Se não encontrar, retornar a primeira
    return routes[0] if routes else None


def display_map(origin_coords, dest_coords, routes, origin_name, dest_name):
    """
    Exibe o mapa com as rotas
    
    Args:
        origin_coords: Coordenadas da origem
        dest_coords: Coordenadas do destino
        routes: Lista de rotas
        origin_name: Nome da origem
        dest_name: Nome do destino
    """
    origin_lat, origin_lon = origin_coords
    dest_lat, dest_lon = dest_coords
    
    # Criar mapa com todas as rotas
    route_map = create_route_map(
        origin_lat, origin_lon,
        dest_lat, dest_lon,
        routes,
        origin_name,
        dest_name
    )
    
    # Exibir mapa
    st.subheader("🗺️ Visualização da Rota")
    folium_static(route_map, width=config.MAP_WIDTH, height=config.MAP_HEIGHT)


def main():
    """Função principal da aplicação"""
    
    # Inicializar serviços
    geocoding_service, backend_client = initialize_services()
    
    # Exibir cabeçalho
    show_header()
    
    # Mostrar sidebar com informações
    status_placeholder = show_sidebar_info()
    
    # Verificar status do back-end
    backend_status = check_backend_status(backend_client, status_placeholder)
    
    if backend_status:
        status_placeholder.success("✅ Back-end conectado")
    else:
        status_placeholder.error("❌ Back-end indisponível (timeout)")
        show_warning(
            "O servidor não respondeu em 3 minutos. "
            "Verifique o painel do Render ou tente novamente em instantes."
        )
        # Não bloqueia: o usuário ainda pode tentar enviar o formulário,
        # pois o back-end pode estar no meio do cold start agora.
    
    # Exibir formulário de entrada
    form_data = show_input_form()
    
    # Processar formulário quando submetido
    if form_data:
        origin = form_data.get('origin', '').strip()
        destination = form_data.get('destination', '').strip()
        criteria = form_data.get('criteria', 'fastest')
        
        # Validar entrada
        if not origin or not destination:
            show_error("Por favor, preencha origem e destino")
            return
        
        # Verificar se back-end está disponível.
        # Se o wake_up ainda não concluiu, tentamos a rota mesmo assim —
        # a requisição ao /route/calculate tem seu próprio timeout generoso.
        if not backend_status:
            show_warning(
                "O servidor pode ainda estar inicializando. Tentando mesmo assim..."
            )
        
        # Geocodificar endereços
        vehicle_type = form_data.get('vehicle_type', 'car')
        coords_result = geocode_addresses(geocoding_service, origin, destination, vehicle_type)
        
        if coords_result is None:
            return
        
        origin_coords, dest_coords, estado_uf = coords_result
        
        # Calcular rotas
        result = calculate_routes(backend_client, form_data, origin_coords, dest_coords)
        
        if result is None:
            return
        
        # Extrair rotas
        routes = result.get('routes', [])
        
        if not routes or len(routes) == 0:
            show_error("Nenhuma rota foi calculada")
            return
        
        # Exibir sucesso
        show_success(f"✅ {len(routes)} rota(s) calculada(s) com sucesso!")
        
        st.divider()
        
        # Encontrar rota selecionada
        selected_route = find_selected_route(routes, criteria)
        
        if selected_route:
            # Exibir resumo da rota selecionada
            show_route_summary(selected_route, criteria)
            
            st.divider()
        
        # Exibir comparação se houver múltiplas rotas
        if len(routes) > 1:
            show_all_routes_comparison(routes)
            st.divider()
        
        # Exibir mapa
        display_map(origin_coords, dest_coords, routes, origin, destination)

        # ---- Estimativa de custo com combustível --------------------------------
        fuel_key = form_data.get('fuel_type', 'gasolina_comum')
        distance_km = selected_route.get('distance_km', 0.0) if selected_route else 0.0

        st.divider()
        with st.spinner("⛽ Consultando preços de combustível..."):
            comparison = fuel_service.build_cost_comparison(distance_km, fuel_key, estado_uf)

        show_fuel_comparison(comparison)
        # -------------------------------------------------------------------------

        # Opção para mostrar dados brutos
        with st.expander("🔍 Ver dados brutos da resposta"):
            st.json(result)
    
    # Exibir rodapé
    show_footer()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Erro crítico na aplicação: {str(e)}")
        st.exception(e)
