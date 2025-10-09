"""
Provider service for handling external insurance provider API calls
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
import structlog
from app.models.providers import Provider

logger = structlog.get_logger()

class ProviderService:
    """Service for handling external provider API interactions"""
    
    def __init__(self):
        self.timeout = 30.0
    
    async def verify_insurance(
        self,
        provider_config: Provider,
        verification_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify insurance with external provider
        """
        try:
            # Prepare request headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Insurance-Verification-System/1.0"
            }
            
            # Add API key if available
            if provider_config.api_key:
                headers["Authorization"] = f"Bearer {provider_config.api_key}"
            
            # Make API call with timeout
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    provider_config.api_endpoint,
                    json=verification_request,
                    headers=headers
                )
                
                # Handle response
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return {
                        "status": "not_found",
                        "message": "Insurance not found",
                        "verified": False
                    }
                elif response.status_code == 401:
                    logger.error("Provider API authentication failed", provider=provider_config.name)
                    raise Exception("Provider authentication failed")
                else:
                    logger.error("Provider API error", 
                               provider=provider_config.name, 
                               status_code=response.status_code)
                    raise Exception(f"Provider API error: {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.error("Provider API timeout", provider=provider_config.name)
            raise Exception("Provider API timeout")
        except httpx.RequestError as e:
            logger.error("Provider API request error", provider=provider_config.name, error=str(e))
            raise Exception(f"Provider API request failed: {str(e)}")
        except Exception as e:
            logger.error("Provider verification failed", provider=provider_config.name, error=str(e))
            raise
    
    async def test_provider_connection(self, provider_config: Provider) -> bool:
        """
        Test connection to provider API
        """
        try:
            headers = {
                "User-Agent": "Insurance-Verification-System/1.0"
            }
            
            if provider_config.api_key:
                headers["Authorization"] = f"Bearer {provider_config.api_key}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try a health check endpoint or simple GET request
                response = await client.get(
                    provider_config.api_endpoint.replace("/verify", "/health"),
                    headers=headers
                )
                
                return response.status_code in [200, 404]  # 404 is ok if health endpoint doesn't exist
                
        except Exception as e:
            logger.error("Provider connection test failed", provider=provider_config.name, error=str(e))
            return False
    
    def get_provider_configuration(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        Get provider-specific configuration
        """
        # This would typically come from the database or configuration
        provider_configs = {
            "provider_a": {
                "endpoint": "https://api.provider-a.com/verify",
                "timeout": 30,
                "retry_count": 3
            },
            "provider_b": {
                "endpoint": "https://api.provider-b.com/verify",
                "timeout": 25,
                "retry_count": 2
            }
        }
        
        return provider_configs.get(provider_name.lower())
