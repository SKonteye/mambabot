"""
Permission manager for handling Claude tool usage approvals via Telegram.
Allows users to approve or deny tool usage through inline buttons.
"""

import asyncio
import logging
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PermissionRequest:
    """Represents a permission request for tool usage."""
    tool_name: str
    tool_input: str
    timestamp: datetime
    message_id: Optional[int] = None
    approved: Optional[bool] = None
    response_event: asyncio.Event = None

    def __post_init__(self):
        if self.response_event is None:
            self.response_event = asyncio.Event()


class PermissionManager:
    """Manages permission requests for Claude tool usage."""

    def __init__(self):
        """Initialize the permission manager."""
        self.pending_requests: Dict[str, PermissionRequest] = {}
        self.timeout = 300.0  # 5 minutes default timeout

    def create_request(self, tool_name: str, tool_input: str) -> str:
        """
        Create a new permission request.

        Args:
            tool_name: Name of the tool requesting permission
            tool_input: Input parameters for the tool

        Returns:
            Request ID
        """
        request_id = f"{tool_name}_{datetime.now().timestamp()}"
        request = PermissionRequest(
            tool_name=tool_name,
            tool_input=tool_input,
            timestamp=datetime.now()
        )
        self.pending_requests[request_id] = request
        logger.info(f"Created permission request: {request_id}")
        return request_id

    async def wait_for_approval(self, request_id: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for user approval on a permission request.

        Args:
            request_id: The request ID to wait for
            timeout: Maximum time to wait (uses default if None)

        Returns:
            True if approved, False if denied or timeout
        """
        if request_id not in self.pending_requests:
            logger.error(f"Request {request_id} not found")
            return False

        request = self.pending_requests[request_id]
        timeout = timeout or self.timeout

        try:
            # Wait for response with timeout
            await asyncio.wait_for(request.response_event.wait(), timeout=timeout)
            return request.approved or False
        except asyncio.TimeoutError:
            logger.warning(f"Permission request {request_id} timed out")
            self.pending_requests.pop(request_id, None)
            return False

    def approve_request(self, request_id: str) -> bool:
        """
        Approve a permission request.

        Args:
            request_id: The request ID to approve

        Returns:
            True if successful, False otherwise
        """
        if request_id not in self.pending_requests:
            logger.error(f"Request {request_id} not found")
            return False

        request = self.pending_requests[request_id]
        request.approved = True
        request.response_event.set()
        logger.info(f"Approved permission request: {request_id}")
        return True

    def deny_request(self, request_id: str) -> bool:
        """
        Deny a permission request.

        Args:
            request_id: The request ID to deny

        Returns:
            True if successful, False otherwise
        """
        if request_id not in self.pending_requests:
            logger.error(f"Request {request_id} not found")
            return False

        request = self.pending_requests[request_id]
        request.approved = False
        request.response_event.set()
        logger.info(f"Denied permission request: {request_id}")
        return True

    def get_request(self, request_id: str) -> Optional[PermissionRequest]:
        """
        Get a permission request by ID.

        Args:
            request_id: The request ID

        Returns:
            PermissionRequest if found, None otherwise
        """
        return self.pending_requests.get(request_id)

    def set_message_id(self, request_id: str, message_id: int):
        """
        Set the Telegram message ID for a permission request.

        Args:
            request_id: The request ID
            message_id: Telegram message ID
        """
        if request_id in self.pending_requests:
            self.pending_requests[request_id].message_id = message_id

    def cleanup_request(self, request_id: str):
        """
        Remove a permission request from pending list.

        Args:
            request_id: The request ID to cleanup
        """
        if request_id in self.pending_requests:
            self.pending_requests.pop(request_id)
            logger.info(f"Cleaned up permission request: {request_id}")


# Global permission manager instance
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """
    Get the global permission manager instance.

    Returns:
        PermissionManager instance
    """
    global _permission_manager

    if _permission_manager is None:
        _permission_manager = PermissionManager()

    return _permission_manager
