"""
Componentes de layout da interface Streamlit
"""

import streamlit as st
from typing import Optional, Dict, Any


def show_header():
    """Exibe o cabeçalho da aplicação"""
    st.title("🗺️ OpenRoute Navigator")
    st.markdown("""
    **Navegação inteligente com múltiplos critérios de rota**
    
    Encontre a melhor rota baseada em:
    - 🚗 Velocidade (rota mais rápida)
    - 🛣️ Qualidade do pavimento
    - 🛡️ Segurança (iluminação e condições)
    - 🚛 Compatibilidade para caminhões
    """)
    st.divider()


def show_input_form() -> Dict[str, Any]:
    """
    Exibe formulário de entrada e retorna os dados preenchidos
    
    Returns:
        Dict com os dados do formulário
    """
    with st.form("route_form"):
        st.subheader("📍 Defina sua rota")
        
        # Campos de origem e destino
        col1, col2 = st.columns(2)
        
        with col1:
            origin = st.text_input(
                "Origem",
                placeholder="Ex: UFRN, Natal, RN",
                help="Digite o endereço de partida"
            )
        
        with col2:
            destination = st.text_input(
                "Destino",
                placeholder="Ex: Ponta Negra, Natal, RN",
                help="Digite o endereço de destino"
            )
        
        # Seleção de critério de rota
        st.subheader("🎯 Critério de rota")
        
        criteria = st.selectbox(
            "Selecione o critério principal",
            options=[
                ("fastest", "🚗 Mais Rápida"),
                ("best_surface", "🛣️ Melhor Pavimento"),
                ("safest", "🛡️ Mais Segura"),
                ("truck_compatible", "🚛 Compatível com Caminhão")
            ],
            format_func=lambda x: x[1],
            help="Escolha o critério mais importante para sua viagem"
        )
        
        # Opções avançadas (truck)
        advanced_options = {}
        
        if criteria[0] == "truck_compatible":
            st.subheader("🚛 Dados do veículo")
            
            col3, col4 = st.columns(2)
            
            with col3:
                height = st.number_input(
                    "Altura (metros)",
                    min_value=0.0,
                    max_value=10.0,
                    value=4.2,
                    step=0.1,
                    help="Altura máxima do caminhão"
                )
                advanced_options['height'] = height
            
            with col4:
                weight = st.number_input(
                    "Peso (toneladas)",
                    min_value=0.0,
                    max_value=100.0,
                    value=28.0,
                    step=0.5,
                    help="Peso total do caminhão"
                )
                advanced_options['weight'] = weight
        
        # Botão de submissão
        st.divider()
        submitted = st.form_submit_button(
            "🔍 Calcular Rota",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            return {
                'origin': origin,
                'destination': destination,
                'criteria': criteria[0],
                'vehicle_type': 'truck' if criteria[0] == 'truck_compatible' else 'car',
                **advanced_options
            }
    
    return None


def show_loading(message: str = "Processando..."):
    """
    Exibe indicador de carregamento
    
    Args:
        message: Mensagem a ser exibida
    """
    with st.spinner(message):
        return st.empty()


def show_loading_with_vehicle(message: str = "Processando...", vehicle_type: str = "car"):
    """
    Exibe indicador de carregamento com ícone específico do veículo
    Modifica o ícone que aparece no canto superior direito do Streamlit
    
    Args:
        message: Mensagem a ser exibida
        vehicle_type: Tipo de veículo ('car', 'motorcycle', 'truck')
    """
    # Mapear tipo de veículo para emoji
    vehicle_icons = {
        'car': '🚗',
        'motorcycle': '🏍️',
        'truck': '🚛'
    }
    
    # Obter emoji apropriado (padrão: carro)
    emoji = vehicle_icons.get(vehicle_type, '🚗')
    
    # CSS customizado para substituir o ícone de loading do Streamlit no canto superior direito
    custom_css = f"""
    <style>
        /* Esconder o ícone padrão do Streamlit */
        .stApp [data-testid="stStatusWidget"] svg {{
            display: none !important;
        }}
        
        /* Adicionar emoji personalizado */
        .stApp [data-testid="stStatusWidget"]::before {{
            content: "{emoji}";
            font-size: 24px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }}
        
        /* Animação de rotação */
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """
    
    # Injetar CSS customizado
    st.markdown(custom_css, unsafe_allow_html=True)
    
    # Exibir spinner com mensagem
    with st.spinner(message):
        return st.empty()



def show_error(message: str, icon: str = "🚨"):
    """
    Exibe mensagem de erro
    
    Args:
        message: Mensagem de erro
        icon: Ícone a ser exibido
    """
    st.error(f"{icon} {message}", icon="🚨")


def show_warning(message: str, icon: str = "⚠️"):
    """
    Exibe mensagem de aviso
    
    Args:
        message: Mensagem de aviso
        icon: Ícone a ser exibido
    """
    st.warning(f"{icon} {message}", icon="⚠️")


def show_success(message: str, icon: str = "✅"):
    """
    Exibe mensagem de sucesso
    
    Args:
        message: Mensagem de sucesso
        icon: Ícone a ser exibido
    """
    st.success(f"{icon} {message}", icon="✅")


def show_info(message: str, icon: str = "ℹ️"):
    """
    Exibe mensagem informativa
    
    Args:
        message: Mensagem informativa
        icon: Ícone a ser exibido
    """
    st.info(f"{icon} {message}", icon="ℹ️")


def show_route_summary(route_data: Dict[str, Any], route_type: str):
    """
    Exibe resumo da rota calculada
    
    Args:
        route_data: Dados da rota
        route_type: Tipo da rota
    """
    route_names = {
        'fastest': '🚗 Rota Mais Rápida',
        'best_surface': '🛣️ Melhor Pavimento',
        'safest': '🛡️ Rota Mais Segura',
        'truck_compatible': '🚛 Compatível com Caminhão'
    }
    
    st.subheader(route_names.get(route_type, 'Rota'))
    
    # Métricas principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Distância",
            f"{route_data.get('distance_km', 0):.2f} km"
        )
    
    with col2:
        alerts = route_data.get('alerts', [])
        alert_count = len(alerts)
        st.metric(
            "Alertas",
            alert_count,
            delta=None if alert_count == 0 else f"{alert_count} avisos",
            delta_color="inverse"
        )
    
    with col3:
        # Calcular status baseado em alertas
        if alert_count == 0:
            status = "✅ Livre"
            status_color = "green"
        elif alert_count <= 2:
            status = "⚠️ Atenção"
            status_color = "orange"
        else:
            status = "🚨 Cuidado"
            status_color = "red"
        
        st.markdown(f"**Status:** {status}")
    
    # Resumo textual
    summary = route_data.get('summary', '')
    if summary:
        st.info(summary)
    
    # Mostrar alertas se houver
    if alerts and len(alerts) > 0:
        with st.expander(f"⚠️ Ver {len(alerts)} alerta(s)", expanded=False):
            for i, alert in enumerate(alerts, 1):
                level = alert.get('level', 'yellow')
                message = alert.get('message', 'Alerta')
                location = alert.get('location', {})
                
                # Determinar ícone baseado no nível
                if level == 'red':
                    icon = "🔴"
                elif level == 'yellow':
                    icon = "🟡"
                else:
                    icon = "🟢"
                
                st.markdown(f"{icon} **Alerta {i}:** {message}")
                if location:
                    lat = location.get('lat', '')
                    lon = location.get('lon', '')
                    if lat and lon:
                        st.caption(f"Localização: {lat:.4f}, {lon:.4f}")


def show_all_routes_comparison(routes: list):
    """
    Exibe comparação entre todas as rotas disponíveis
    
    Args:
        routes: Lista de rotas calculadas
    """
    if not routes or len(routes) == 0:
        return
    
    st.subheader("📊 Comparação de Rotas")
    
    route_names = {
        'fastest': '🚗 Mais Rápida',
        'best_surface': '🛣️ Melhor Pavimento',
        'safest': '🛡️ Mais Segura',
        'truck_compatible': '🚛 Caminhão'
    }
    
    # Criar tabela comparativa
    comparison_data = []
    
    for route in routes:
        route_type = route.get('type', 'unknown')
        comparison_data.append({
            'Rota': route_names.get(route_type, route_type),
            'Distância (km)': f"{route.get('distance_km', 0):.2f}",
            'Alertas': len(route.get('alerts', []))
        })
    
    st.table(comparison_data)


def show_sidebar_info():
    """Exibe informações na barra lateral"""
    with st.sidebar:
        st.header("ℹ️ Sobre")
        
        st.markdown("""
        **OpenRoute Navigator** é uma ferramenta de planejamento de rotas 
        que utiliza dados do OpenStreetMap para encontrar o melhor caminho 
        baseado em diferentes critérios.
        
        ### Critérios disponíveis:
        
        - **Mais Rápida:** Menor tempo de viagem
        - **Melhor Pavimento:** Prioriza vias bem pavimentadas
        - **Mais Segura:** Considera iluminação e condições da via
        - **Caminhão:** Verifica restrições de altura e peso
        
        ### Como usar:
        
        1. Digite origem e destino
        2. Escolha o critério de rota
        3. Clique em "Calcular Rota"
        4. Visualize o resultado no mapa
        """)
        
        st.divider()
        
        st.markdown("""
        ### 🔧 Status do Back-End
        """)
        
        # Placeholder para status (será atualizado pela aplicação principal)
        return st.empty()


def show_footer():
    """Exibe rodapé da aplicação"""
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>OpenRoute Navigator MVP • Desenvolvido com Streamlit e Folium</p>
        <p>Dados: OpenStreetMap • API: OpenRouteService</p>
    </div>
    """, unsafe_allow_html=True)
