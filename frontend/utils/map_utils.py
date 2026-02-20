"""
Utilitários para criação e estilização de mapas Folium
"""

import folium
from typing import List, Tuple, Dict, Any, Optional


# Definição de cores para diferentes critérios de rota
ROUTE_COLORS = {
    'fastest': '#2E7D32',        # Verde escuro - rota mais rápida
    'best_surface': '#1976D2',   # Azul - melhor pavimento
    'safest': '#00897B',         # Teal - rota mais segura
    'truck_compatible': '#F57C00' # Laranja - compatível com caminhão
}

# Cores de alerta
ALERT_COLORS = {
    'red': '#D32F2F',      # Vermelho - crítico
    'yellow': '#FFA000',   # Amarelo/Laranja - atenção
    'green': '#388E3C'     # Verde - OK
}


def create_base_map(
    center_lat: float,
    center_lon: float,
    zoom_start: int = 13
) -> folium.Map:
    """
    Cria um mapa base Folium
    
    Args:
        center_lat: Latitude do centro do mapa
        center_lon: Longitude do centro do mapa
        zoom_start: Nível de zoom inicial
        
    Returns:
        Objeto folium.Map configurado
    """
    # Criar mapa com OpenStreetMap como camada base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Adicionar Stadia.StamenTonerBlacklite
    folium.TileLayer(
        tiles='https://tiles.stadiamaps.com/tiles/stamen_toner_blacklite/{z}/{x}/{y}{r}.png',
        attr=(
            '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> '
            '&copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> '
            '&copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> '
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        ),
        name='Stadia Toner Blacklite',
        overlay=False,
        control=True,
        min_zoom=0,
        max_zoom=20
    ).add_to(m)
    
    # Adicionar Esri.WorldImagery
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr=(
            'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, '
            'Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
        ),
        name='Esri World Imagery',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Adicionar controle de camadas
    folium.LayerControl().add_to(m)
    
    return m


def add_marker(
    map_obj: folium.Map,
    lat: float,
    lon: float,
    popup_text: str,
    tooltip_text: str,
    icon: str = 'info-sign',
    color: str = 'blue'
) -> folium.Map:
    """
    Adiciona um marcador ao mapa
    
    Args:
        map_obj: Objeto do mapa Folium
        lat: Latitude do marcador
        lon: Longitude do marcador
        popup_text: Texto do popup (clique)
        tooltip_text: Texto do tooltip (hover)
        icon: Ícone do marcador
        color: Cor do marcador
        
    Returns:
        Mapa atualizado
    """
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=tooltip_text,
        icon=folium.Icon(color=color, icon=icon)
    ).add_to(map_obj)
    
    return map_obj


def add_route_line(
    map_obj: folium.Map,
    geometry: List[List[float]],
    route_type: str,
    distance_km: float,
    alerts: List[Dict[str, Any]],
    popup_info: Optional[str] = None
) -> folium.Map:
    """
    Adiciona uma linha de rota ao mapa
    
    Args:
        map_obj: Objeto do mapa
        geometry: Lista de coordenadas [[lon, lat], [lon, lat], ...]
        route_type: Tipo da rota (fastest, best_surface, etc.)
        distance_km: Distância em km
        alerts: Lista de alertas da rota
        popup_info: Informações adicionais para o popup
        
    Returns:
        Mapa atualizado
    """
    # Converter geometria de [lon, lat] para [lat, lon]
    coordinates = [[point[1], point[0]] for point in geometry]
    
    # Determinar cor baseada no tipo de rota
    color = ROUTE_COLORS.get(route_type, '#666666')
    
    # Definir peso da linha baseado em alertas
    weight = 5
    if alerts and len(alerts) > 0:
        # Linhas com alertas são mais grossas para destaque
        weight = 6
    
    # Criar texto do popup
    route_names = {
        'fastest': 'Rota Mais Rápida',
        'best_surface': 'Melhor Pavimento',
        'safest': 'Rota Mais Segura',
        'truck_compatible': 'Compatível com Caminhão'
    }
    
    popup_html = f"""
    <div style="font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0; color: {color};">
            {route_names.get(route_type, route_type.title())}
        </h4>
        <p style="margin: 5px 0;"><strong>Distância:</strong> {distance_km:.2f} km</p>
        <p style="margin: 5px 0;"><strong>Alertas:</strong> {len(alerts)}</p>
    """
    
    if popup_info:
        popup_html += f"<p style='margin: 5px 0;'>{popup_info}</p>"
    
    # Adicionar informações de alertas
    if alerts and len(alerts) > 0:
        popup_html += "<hr style='margin: 10px 0;'>"
        popup_html += "<p style='margin: 5px 0;'><strong>Avisos:</strong></p>"
        popup_html += "<ul style='margin: 5px 0; padding-left: 20px;'>"
        for alert in alerts[:3]:  # Mostrar até 3 alertas
            level = alert.get('level', 'yellow')
            message = alert.get('message', 'Alerta')
            popup_html += f"<li style='color: {ALERT_COLORS.get(level, '#000')};'>{message}</li>"
        if len(alerts) > 3:
            popup_html += f"<li>... e mais {len(alerts) - 3} alertas</li>"
        popup_html += "</ul>"
    
    popup_html += "</div>"
    
    # Adicionar linha ao mapa
    folium.PolyLine(
        locations=coordinates,
        color=color,
        weight=weight,
        opacity=0.8,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{route_names.get(route_type, route_type.title())} - {distance_km:.2f} km"
    ).add_to(map_obj)
    
    return map_obj


def add_alert_markers(
    map_obj: folium.Map,
    alerts: List[Dict[str, Any]]
) -> folium.Map:
    """
    Adiciona marcadores de alerta no mapa
    
    Args:
        map_obj: Objeto do mapa
        alerts: Lista de alertas com informações de localização
        
    Returns:
        Mapa atualizado
    """
    for alert in alerts:
        location = alert.get('location')
        if not location:
            continue
        
        lat = location.get('lat')
        lon = location.get('lon')
        level = alert.get('level', 'yellow')
        message = alert.get('message', 'Alerta')
        
        # Determinar cor e ícone baseado no nível
        if level == 'red':
            color = 'red'
            icon = 'exclamation-sign'
        elif level == 'yellow':
            color = 'orange'
            icon = 'warning-sign'
        else:
            color = 'green'
            icon = 'info-sign'
        
        # Adicionar marcador circular
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            popup=message,
            tooltip=message,
            color=ALERT_COLORS[level],
            fill=True,
            fillColor=ALERT_COLORS[level],
            fillOpacity=0.6
        ).add_to(map_obj)
    
    return map_obj


def create_route_map(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    routes: List[Dict[str, Any]],
    origin_name: str = "Origem",
    dest_name: str = "Destino"
) -> folium.Map:
    """
    Cria um mapa completo com origem, destino e múltiplas rotas
    
    Args:
        origin_lat: Latitude da origem
        origin_lon: Longitude da origem
        dest_lat: Latitude do destino
        dest_lon: Longitude do destino
        routes: Lista de rotas calculadas
        origin_name: Nome da origem
        dest_name: Nome do destino
        
    Returns:
        Mapa Folium completo
    """
    # Calcular ponto central entre origem e destino
    center_lat = (origin_lat + dest_lat) / 2
    center_lon = (origin_lon + dest_lon) / 2
    
    # Criar mapa base
    m = create_base_map(center_lat, center_lon, zoom_start=12)
    
    # Adicionar marcador de origem (azul)
    add_marker(
        m, origin_lat, origin_lon,
        popup_text=f"<b>Origem</b><br>{origin_name}",
        tooltip_text=origin_name,
        icon='play',
        color='blue'
    )
    
    # Adicionar marcador de destino (vermelho)
    add_marker(
        m, dest_lat, dest_lon,
        popup_text=f"<b>Destino</b><br>{dest_name}",
        tooltip_text=dest_name,
        icon='stop',
        color='red'
    )
    
    # Adicionar rotas
    for route in routes:
        geometry = route.get('geometry', [])
        route_type = route.get('type', 'unknown')
        distance_km = route.get('distance_km', 0)
        alerts = route.get('alerts', [])
        summary = route.get('summary', '')
        
        if geometry:
            add_route_line(
                m, geometry, route_type, distance_km, alerts, summary
            )
            
            # Adicionar marcadores de alerta
            if alerts:
                add_alert_markers(m, alerts)
    
    # Ajustar zoom para incluir todos os pontos
    try:
        m.fit_bounds([[origin_lat, origin_lon], [dest_lat, dest_lon]])
    except:
        pass  # Se falhar, manter zoom padrão
    
    return m


def create_simple_route_map(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    route_data: Dict[str, Any],
    origin_name: str = "Origem",
    dest_name: str = "Destino"
) -> folium.Map:
    """
    Cria um mapa com uma única rota
    
    Args:
        origin_lat, origin_lon: Coordenadas da origem
        dest_lat, dest_lon: Coordenadas do destino
        route_data: Dados da rota
        origin_name, dest_name: Nomes dos locais
        
    Returns:
        Mapa Folium
    """
    return create_route_map(
        origin_lat, origin_lon, dest_lat, dest_lon,
        [route_data], origin_name, dest_name
    )
