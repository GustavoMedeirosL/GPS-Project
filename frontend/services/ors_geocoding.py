"""
OpenRouteService Geocoding Service

Converte endereços de texto em coordenadas geográficas (latitude, longitude)
usando a API de geocoding do OpenRouteService.
"""

import requests
from typing import Dict, Optional, Tuple
import time


class ORSGeocodingService:
    """Serviço de geocodificação usando OpenRouteService API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o serviço de geocoding
        
        Args:
            api_key: Chave da API OpenRouteService (opcional para uso público limitado)
        """
        self.base_url = "https://api.openrouteservice.org/geocode/search"
        self.api_key = api_key
        self.session = requests.Session()
        
        # Configurar headers se houver API key
        if self.api_key:
            self.session.headers.update({
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            })
    
    def geocode(self, address: str, timeout: int = 10) -> Tuple[float, float]:
        """
        Converte um endereço em coordenadas geográficas
        
        Args:
            address: Endereço completo ou descrição do local
            timeout: Tempo máximo de espera pela resposta (segundos)
            
        Returns:
            Tuple[float, float]: (latitude, longitude)
            
        Raises:
            ValueError: Se o endereço não for encontrado
            ConnectionError: Se houver falha na conexão com a API
            TimeoutError: Se a requisição exceder o timeout
        """
        if not address or not address.strip():
            raise ValueError("Endereço não pode estar vazio")
        
        try:
            # Parâmetros da requisição
            params = {
                'text': address.strip(),
                'size': 1  # Retornar apenas o melhor resultado
            }
            
            # Adicionar API key nos parâmetros se disponível
            if self.api_key:
                params['api_key'] = self.api_key
            
            # Fazer requisição
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=timeout
            )
            
            # Verificar status da resposta
            if response.status_code == 401:
                raise ConnectionError("API key inválida ou não autorizada")
            elif response.status_code == 429:
                raise ConnectionError("Limite de requisições excedido. Aguarde alguns minutos.")
            elif response.status_code != 200:
                raise ConnectionError(f"Erro na API: Status {response.status_code}")
            
            # Parsear resposta
            data = response.json()
            
            # Verificar se encontrou resultados
            if not data.get('features') or len(data['features']) == 0:
                raise ValueError(f"Endereço não encontrado: '{address}'")
            
            # Extrair coordenadas do primeiro resultado
            coordinates = data['features'][0]['geometry']['coordinates']
            lon, lat = coordinates[0], coordinates[1]
            
            return (lat, lon)
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Timeout ao buscar o endereço: '{address}'")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Falha na conexão com o serviço de geocoding")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Erro na requisição: {str(e)}")
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"Resposta da API mal formatada: {str(e)}")
    
    def geocode_batch(self, addresses: list) -> Dict[str, Tuple[float, float]]:
        """
        Geocodifica múltiplos endereços
        
        Args:
            addresses: Lista de endereços
            
        Returns:
            Dict com endereço como chave e (lat, lon) como valor
        """
        results = {}
        
        for address in addresses:
            try:
                coords = self.geocode(address)
                results[address] = coords
                # Pequeno delay para evitar rate limiting
                time.sleep(0.5)
            except Exception as e:
                results[address] = None
                print(f"Erro ao geocodificar '{address}': {str(e)}")
        
        return results
    
    def get_location_name(self, lat: float, lon: float, timeout: int = 10) -> str:
        """
        Reverse geocoding: converte coordenadas em nome do local
        
        Args:
            lat: Latitude
            lon: Longitude
            timeout: Tempo máximo de espera
            
        Returns:
            Nome do local encontrado
        """
        try:
            url = "https://api.openrouteservice.org/geocode/reverse"
            
            params = {
                'point.lat': lat,
                'point.lon': lon,
                'size': 1
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                return data['features'][0]['properties'].get('label', 'Local desconhecido')
            
            return f"Coordenadas: {lat:.4f}, {lon:.4f}"
            
        except Exception as e:
            return f"Coordenadas: {lat:.4f}, {lon:.4f}"


# Criar instância global (sem API key para uso público)
geocoding_service = ORSGeocodingService()


def geocode_address(address: str) -> Tuple[float, float]:
    """
    Função utilitária para geocodificar um endereço
    
    Args:
        address: Endereço a ser geocodificado
        
    Returns:
        Tuple[float, float]: (latitude, longitude)
    """
    return geocoding_service.geocode(address)
