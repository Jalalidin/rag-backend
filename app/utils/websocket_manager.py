"""
WebSocket Manager Module

This module provides real-time WebSocket connection management for chat functionality.
It handles:
- Connection management for multiple chat sessions
- Real-time message broadcasting
- Typing indicator status tracking and broadcasting
- Graceful connection handling and cleanup

The manager maintains separate connection pools for each chat session and
tracks typing status for all active users.
"""

from typing import Dict, Set
from fastapi import WebSocket
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages WebSocket connections and real-time communication for chat sessions.
    
    This class maintains:
    - Active WebSocket connections grouped by chat session
    - Typing status for users in each chat session
    - Mapping between WebSocket connections and user/chat information
    
    It provides methods for connection handling, message broadcasting,
    and typing status management.
    """
    
    def __init__(self):
        """
        Initialize the WebSocket manager with connection tracking dictionaries.
        
        Attributes:
            active_connections: Maps chat_id to set of active WebSocket connections
            typing_users: Maps chat_id to set of currently typing user IDs
            connection_map: Maps WebSocket instances to (chat_id, user_id) pairs
        """
        # chat_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = defaultdict(set)
        # chat_id -> set of typing user_ids
        self.typing_users: Dict[int, Set[int]] = defaultdict(set)
        # websocket -> (chat_id, user_id) mapping for quick lookups
        self.connection_map: Dict[WebSocket, tuple[int, int]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """
        Establish a new WebSocket connection for a chat session.
        
        Args:
            websocket: The WebSocket connection to establish
            chat_id: ID of the chat session
            user_id: ID of the connecting user
            
        This method:
        1. Accepts the WebSocket connection
        2. Adds it to the active connections for the chat
        3. Updates the connection mapping
        4. Sends current typing status to the new connection
        """
        await websocket.accept()
        self.active_connections[chat_id].add(websocket)
        self.connection_map[websocket] = (chat_id, user_id)
        
        # Send current typing status to newly connected client
        if self.typing_users[chat_id]:
            await websocket.send_json({
                "type": "typing_status",
                "typing_users": list(self.typing_users[chat_id])
            })

    async def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """
        Handle WebSocket disconnection and cleanup.
        
        Args:
            websocket: The WebSocket connection to close
            chat_id: ID of the chat session
            user_id: ID of the disconnecting user
            
        This method:
        1. Removes the connection from active connections
        2. Cleans up the connection mapping
        3. Updates and broadcasts typing status if needed
        """
        self.active_connections[chat_id].discard(websocket)
        if websocket in self.connection_map:
            del self.connection_map[websocket]
        
        # Clean up typing status and notify other users
        if user_id in self.typing_users[chat_id]:
            self.typing_users[chat_id].remove(user_id)
            await self.broadcast_typing_status(chat_id)

    async def broadcast_message(self, chat_id: int, message: dict):
        """
        Broadcast a message to all connected clients in a chat session.
        
        Args:
            chat_id: ID of the chat session
            message: Dictionary containing the message data to broadcast
            
        Handles connection errors by disconnecting failed connections.
        Messages are sent as JSON to all active connections in the chat.
        """
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
                    await self.disconnect(connection, *self.connection_map[connection])

    async def broadcast_typing(self, chat_id: int, user_id: int, is_typing: bool):
        """
        Update and broadcast a user's typing status.
        
        Args:
            chat_id: ID of the chat session
            user_id: ID of the user whose typing status changed
            is_typing: Whether the user is currently typing
            
        Updates the typing status for the user and broadcasts
        the updated status to all connected clients.
        """
        if is_typing:
            self.typing_users[chat_id].add(user_id)
        else:
            self.typing_users[chat_id].discard(user_id)
        
        await self.broadcast_typing_status(chat_id)

    async def broadcast_typing_status(self, chat_id: int):
        """
        Broadcast current typing status to all clients in a chat.
        
        Args:
            chat_id: ID of the chat session
            
        Sends a typing_status message containing the list of
        currently typing users to all connected clients.
        """
        await self.broadcast_message(chat_id, {
            "type": "typing_status",
            "typing_users": list(self.typing_users[chat_id])
        }) 