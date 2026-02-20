"""
Cliente para comunicação com o back-end FastAPI do OpenRoute Navigator
"""

import requests
from typing import Dict, Optional, List, Any
import time


class BackendClient:
    """Cliente para comunicação com a API back-end"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Inicializa o cliente
        
        Args:
            base_url: URL base da API back-end
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def health_check(self) -> bool:
        """
        Verifica se o back-end está disponível
        
        Returns:
            True se o back-end está respondendo, False caso contrário
        """
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def calculate_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        vehicle_type: str = "car",
        height: Optional[float] = None,
        weight: Optional[float] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Calcula rotas entre origem e destino
        
        Args:
            origin_lat: Latitude da origem
            origin_lon: Longitude da origem
            dest_lat: Latitude do destino
            dest_lon: Longitude do destino
            vehicle_type: Tipo de veículo ("car" ou "truck")
            height: Altura do veículo em metros (apenas para truck)
            weight: Peso do veículo em toneladas (apenas para truck)
            timeout: Tempo máximo de espera pela resposta
            
        Returns:
            Dict contendo as rotas calculadas e informações adicionais
            
        Raises:
            ConnectionError: Se houver falha na comunicação com o back-end
            ValueError: Se a resposta for inválida
            TimeoutError: Se a requisição exceder o timeout
        """
        # Montar payload da requisição
        payload = {
            "origin": {
                "lat": origin_lat,
                "lon": origin_lon
            },
            "destination": {
                "lat": dest_lat,
                "lon": dest_lon
            },
            "vehicle": {
                "vehicle_type": vehicle_type
            }
        }
        
        # Adicionar parâmetros de caminhão se fornecidos
        if vehicle_type == "truck":
            if height is not None:
                payload["vehicle"]["height"] = height
            if weight is not None:
                payload["vehicle"]["weight"] = weight
        
        try:
            # Fazer requisição POST para o endpoint de cálculo de rota
            response = self.session.post(
                f"{self.base_url}/route/calculate",
                json=payload,
                timeout=timeout
            )
            
            # Verificar status da resposta
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 422:
                error_detail = response.json().get('detail', 'Parâmetros inválidos')
                raise ValueError(f"Erro de validação: {error_detail}")
            elif response.status_code == 500:
                raise ConnectionError("Erro interno do servidor")
            else:
                raise ConnectionError(f"Erro na API: Status {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout ao calcular rota. Tente novamente.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Não foi possível conectar ao back-end. "
                "Verifique se o servidor está em execução."
            )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Erro na requisição: {str(e)}")
        except (KeyError, TypeError) as e:
            raise ValueError(f"Resposta mal formatada do servidor: {str(e)}")
    
    def get_route_by_criteria(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        criteria: str,
        vehicle_type: str = "car",
        height: Optional[float] = None,
        weight: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém uma rota específica baseada no critério selecionado
        
        Args:
            origin_lat: Latitude da origem
            origin_lon: Longitude da origem
            dest_lat: Latitude do destino
            dest_lon: Longitude do destino
            criteria: Critério de rota ("fastest", "best_surface", "safest", "truck_compatible")
            vehicle_type: Tipo de veículo
            height: Altura do veículo (truck)
            weight: Peso do veículo (truck)
            
        Returns:
            Dicionário com informações da rota ou None se não encontrada
        """
        # Calcular todas as rotas
        result = self.calculate_route(
            origin_lat, origin_lon, dest_lat, dest_lon,
            vehicle_type, height, weight
        )
        
        # Procurar pela rota do critério especificado
        routes = result.get('routes', [])
        
        for route in routes:
            if route.get('type') == criteria:
                return route
        
        # Se não encontrar, retornar a primeira rota disponível
        return routes[0] if routes else None
    
    def get_all_routes(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        vehicle_type: str = "car",
        height: Optional[float] = None,
        weight: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém todas as rotas disponíveis
        
        Returns:
            Lista de rotas
        """
        result = self.calculate_route(
            origin_lat, origin_lon, dest_lat, dest_lon,
            vehicle_type, height, weight
        )
        
        return result.get('routes', [])


# Criar instância global do cliente
backend_client = BackendClient()


def calculate_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    criteria: str = "fastest",
    vehicle_type: str = "car",
    **kwargs
) -> Dict[str, Any]:
    """
    Função utilitária para calcular uma rota específica
    
    Args:
        origin_lat: Latitude da origem
        origin_lon: Longitude da origem
        dest_lat: Latitude do destino
        dest_lon: Longitude do destino
        criteria: Critério de escolha da rota
        vehicle_type: Tipo de veículo
        **kwargs: Parâmetros adicionais (height, weight)
        
    Returns:
        Dicionário com informações da rota
    """
    return backend_client.get_route_by_criteria(
        origin_lat, origin_lon, dest_lat, dest_lon,
        criteria, vehicle_type,
        kwargs.get('height'), kwargs.get('weight')
    )
