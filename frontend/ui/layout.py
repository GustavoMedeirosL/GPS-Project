"""
Componentes de layout da interface Streamlit
"""

import streamlit as st
from typing import Optional, Dict, Any, List


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
        
        # Seleção de combustível
        st.subheader("⛽ Combustível do veículo")

        FUEL_OPTIONS = [
            ("gasolina_comum",     "⛽ Gasolina Comum"),
            ("gasolina_aditivada", "⛽ Gasolina Aditivada"),
            ("diesel_comum",       "🚛 Diesel Comum"),
            ("diesel_s10",         "🚛 Diesel S10"),
            ("alcool",             "🌿 Álcool (Etanol)"),
        ]

        fuel_type = st.selectbox(
            "Selecione o combustível do seu veículo",
            options=FUEL_OPTIONS,
            format_func=lambda x: x[1],
            help="Usado para estimar o custo da rota e comparar com GNV"
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
                'fuel_type': fuel_type[0],
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
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:10px;
                    padding:10px 16px; border-radius:8px;
                    background:#1e293b; color:#cbd5e1; font-size:15px;">
            <span style="animation:spin 1s linear infinite; display:inline-block;">⏳</span>
            {message}
        </div>
        <style>@keyframes spin{{0%{{transform:rotate(0deg)}}100%{{transform:rotate(360deg)}}}}</style>
        """,
        unsafe_allow_html=True,
    )


def show_loading_with_vehicle(message: str = "Processando...", vehicle_type: str = "car"):
    """
    Exibe indicador de carregamento com ícone específico do veículo.

    Args:
        message: Mensagem a ser exibida
        vehicle_type: Tipo de veículo ('car', 'motorcycle', 'truck')
    """
    vehicle_icons = {
        'car': '🚗',
        'motorcycle': '🏍️',
        'truck': '🚛'
    }
    emoji = vehicle_icons.get(vehicle_type, '🚗')

    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:12px;
                    padding:10px 16px; border-radius:8px;
                    background:#1e293b; color:#cbd5e1; font-size:15px;">
            <span style="font-size:22px;
                         animation:vehicle-bounce 0.6s ease-in-out infinite alternate;
                         display:inline-block;">{emoji}</span>
            {message}
        </div>
        <style>
            @keyframes vehicle-bounce {{
                from {{ transform: translateX(-4px); }}
                to   {{ transform: translateX( 4px); }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )



def show_error(message: str, icon: str = "🚨"):
    """
    Exibe mensagem de erro
    
    Args:
        message: Mensagem de erro
        icon: Ícone a ser exibido
    """
    st.error(message, icon=icon)


def show_warning(message: str, icon: str = "⚠️"):
    """
    Exibe mensagem de aviso
    
    Args:
        message: Mensagem de aviso
        icon: Ícone a ser exibido
    """
    st.warning(message, icon=icon)


def show_success(message: str, icon: str = "✅"):
    """
    Exibe mensagem de sucesso
    
    Args:
        message: Mensagem de sucesso
        icon: Ícone a ser exibido
    """
    st.success(message, icon=icon)


def show_info(message: str, icon: str = "ℹ️"):
    """
    Exibe mensagem informativa
    
    Args:
        message: Mensagem informativa
        icon: Ícone a ser exibido
    """
    st.info(message, icon=icon)


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


def show_fuel_comparison(data: Optional[Dict[str, Any]]):
    """
    Exibe o quadro comparativo de custo de combustível vs GNV.

    Args:
        data: Dicionário retornado por fuel_service.build_cost_comparison(),
              ou None se o cálculo não foi possível.
    """
    st.subheader("⛽ Estimativa de Custo com Combustível")

    if data is None:
        st.warning(
            "Não foi possível obter os preços de combustível para esta rota. "
            "Isso pode ocorrer quando o estado de origem não é identificado ou "
            "a API de preços está temporariamente indisponível.",
            icon="⚠️"
        )
        return

    def fmt_brl(value: Optional[float]) -> str:
        if value is None:
            return "—"
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def fmt_num(value: Optional[float], decimals: int = 2) -> str:
        if value is None:
            return "—"
        return f"{value:.{decimals}f}"

    estado_uf   = data.get("estado_uf", "—")
    distance_km = data.get("distance_km", 0.0)
    fuel_label  = data.get("fuel_label", "—")
    unid_sel    = data.get("fuel_unidade", "l")
    consumo_sel = data.get("consumo_sel")
    consumo_gnv = data.get("consumo_gnv")
    preco_sel   = data.get("preco_sel")
    preco_gnv   = data.get("preco_gnv")
    qtd_sel     = data.get("qtd_sel")
    qtd_gnv     = data.get("qtd_gnv")
    custo_sel   = data.get("custo_sel")
    custo_gnv   = data.get("custo_gnv")
    economia    = data.get("economia_pct")

    # ---- Avisos parciais ---------------------------------------------------
    if preco_sel is None:
        st.warning(
            f"Preço de **{fuel_label}** não disponível para **{estado_uf}**. "
            "O custo estimado não pôde ser calculado.",
            icon="⚠️"
        )
    if preco_gnv is None:
        st.info(
            f"Preço do **GNV** não disponível para **{estado_uf}**. "
            "A comparação com GNV não está disponível.",
            icon="ℹ️"
        )

    # ---- Métricas destaque -------------------------------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🗺️ Distância", f"{distance_km:.2f} km")
    with col2:
        st.metric(f"💰 Custo ({fuel_label})", fmt_brl(custo_sel))
    with col3:
        st.metric("💰 Custo (GNV)", fmt_brl(custo_gnv))

    # ---- Tabela comparativa detalhada --------------------------------------
    st.markdown("")

    rows = [
        ("📍 Estado identificado",                   estado_uf),
        (f"⛽ Combustível selecionado",               fuel_label),
        (f"💲 Preço ({fuel_label})",
            f"{fmt_brl(preco_sel)} / {unid_sel}" if preco_sel else "—"),
        ("💲 Preço (GNV)",
            f"{fmt_brl(preco_gnv)} / m³" if preco_gnv else "—"),
        ("🗺️ Distância total",                       f"{distance_km:.2f} km"),
        (f"🔋 Consumo médio ({fuel_label})",
            f"{fmt_num(consumo_sel)} km/{unid_sel}" if consumo_sel else "—"),
        ("🔋 Consumo médio (GNV)",
            f"{fmt_num(consumo_gnv)} km/m³" if consumo_gnv else "—"),
        (f"🧪 Quantidade estimada ({fuel_label})",
            f"{fmt_num(qtd_sel)} {unid_sel}" if qtd_sel else "—"),
        ("🧪 Quantidade estimada (GNV)",
            f"{fmt_num(qtd_gnv)} m³" if qtd_gnv else "—"),
        (f"💰 Custo estimado ({fuel_label})",         fmt_brl(custo_sel)),
        ("💰 Custo estimado (GNV)",                  fmt_brl(custo_gnv)),
    ]

    # Linha de economia (apenas quando disponível)
    if economia is not None:
        economia_str = f"{economia:.2f}%"
        if economia > 0:
            rows.append(("✅ Economia com GNV", economia_str))
        elif economia < 0:
            rows.append(("❌ GNV mais caro neste estado", f"{abs(economia):.2f}% a mais"))
        else:
            rows.append(("➡️ Custo equivalente", "0,00%"))

    # Container estilizado
    with st.container():
        st.markdown(
            """
            <style>
            .fuel-table { width:100%; border-collapse:collapse; font-size:14px; }
            .fuel-table tr:nth-child(even) { background:#1e293b; }
            .fuel-table tr:nth-child(odd)  { background:#0f172a; }
            .fuel-table td { padding:8px 14px; color:#e2e8f0; }
            .fuel-table td:first-child { color:#94a3b8; width:55%; }
            .fuel-table td:last-child  { font-weight:600; text-align:right; }
            .fuel-table tr:last-child td { color:#4ade80; font-size:16px; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        rows_html = "".join(
            f"<tr><td>{label}</td><td>{value}</td></tr>"
            for label, value in rows
        )
        st.markdown(
            f"<table class='fuel-table'>{rows_html}</table>",
            unsafe_allow_html=True,
        )

    if economia is not None and economia > 0:
        st.success(
            f"🌿 Ao usar GNV, você economizaria aproximadamente **{economia:.2f}%** "
            f"({fmt_brl(custo_sel and custo_gnv and custo_sel - custo_gnv)}) nesta rota em **{estado_uf}**."
        )


def show_footer():
    """Exibe rodapé da aplicação"""
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>OpenRoute Navigator MVP • Desenvolvido com Streamlit e Folium</p>
        <p>Dados: OpenStreetMap • API: OpenRouteService</p>
    </div>
    """, unsafe_allow_html=True)
