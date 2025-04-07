"""AWS session management utilities."""
import asyncio
from typing import Dict, Any, Optional, Union
import aioboto3

class AWSSessionManager:
    """Manages AWS sessions and clients to prevent resource leaks."""
    
    def __init__(self):
        self._sessions = {}
        self._clients = {}
    
    async def get_client(self, 
                        service_name: str, 
                        region_name: str, 
                        session_args: Dict[str, Any]) -> Any:
        """
        Get a boto3 client for the specified service and region.
        Reuses existing clients when possible.
        
        Args:
            service_name: AWS service name (e.g., 'dynamodb', 'cloudwatch')
            region_name: AWS region name
            session_args: Arguments for creating the session
            
        Returns:
            The boto3 client
        """
        # Create a unique key for this client configuration
        key = f"{service_name}:{region_name}:{hash(frozenset(session_args.items()))}"
        
        # Return existing client if available
        if key in self._clients:
            return self._clients[key]
        
        # Create a new session if needed
        session_key = hash(frozenset(session_args.items()))
        if session_key not in self._sessions:
            self._sessions[session_key] = aioboto3.Session(**session_args)
        
        # Create a new client
        self._clients[key] = await self._sessions[session_key].client(
            service_name, 
            region_name=region_name
        ).__aenter__()
        
        return self._clients[key]
    
    async def close(self):
        """Close all clients and sessions."""
        # Close all clients first
        for key, client in list(self._clients.items()):
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error closing client {key}: {e}")
            self._clients.pop(key, None)
        
        # Clear sessions (they don't need explicit closing)
        self._sessions.clear()
        
        # Allow any remaining aiohttp sessions to complete closing
        await asyncio.sleep(0.5)

# Global session manager instance
session_manager = AWSSessionManager()

async def cleanup_aws_sessions():
    """Clean up all AWS sessions on application shutdown."""
    await session_manager.close()
