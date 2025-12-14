"""Asterisk Manager Interface (AMI) client."""

import asyncio
import logging

from ..config import AsteriskConfig
from ..exceptions import AsteriskError

logger = logging.getLogger("provisioner.asterisk.ami")


class AMIClient:
    """Asterisk Manager Interface client for sending commands and reloading modules."""

    def __init__(self, config: AsteriskConfig):
        """Initialize AMI client.

        Args:
            config: Asterisk configuration
        """
        self.config = config
        self.manager = None
        self._connected = False

    async def connect(self) -> bool:
        """Establish AMI connection.

        Returns:
            True if connection successful, False otherwise
        """
        if self._connected and self.manager:
            return True

        try:
            # Import panoramisk here to avoid import errors if not installed
            try:
                from panoramisk import Manager
            except ImportError:
                logger.error(
                    "panoramisk library not installed. Install with: pip install panoramisk"
                )
                return False

            self.manager = Manager(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                secret=self.config.password,
                ping_delay=30,
                ping_tries=3,
            )

            await self.manager.connect()
            self._connected = True
            logger.info(f"Connected to Asterisk AMI at {self.config.host}:{self.config.port}")
            return True

        except Exception as e:
            logger.error(f"AMI connection failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close AMI connection."""
        if self.manager and self._connected:
            try:
                await self.manager.close()
                logger.info("Disconnected from Asterisk AMI")
            except Exception as e:
                logger.warning(f"Error during AMI disconnect: {e}")
            finally:
                self._connected = False
                self.manager = None

    async def reload_pjsip(self) -> bool:
        """Reload PJSIP module.

        Returns:
            True if reload successful, False otherwise

        Raises:
            AsteriskError: If not connected to AMI
        """
        if not self._connected or not self.manager:
            raise AsteriskError("Not connected to AMI. Call connect() first.")

        try:
            response = await self.manager.send_action({"Action": "PJSIPReload"})

            # Check response
            if hasattr(response, "success") and response.success:
                logger.info("PJSIP module reloaded successfully")
                return True
            elif isinstance(response, dict) and response.get("Response") == "Success":
                logger.info("PJSIP module reloaded successfully")
                return True
            else:
                logger.warning(f"PJSIP reload response: {response}")
                return False

        except Exception as e:
            logger.error(f"PJSIP reload failed: {e}")
            return False

    async def reload_dialplan(self) -> bool:
        """Reload dialplan (extensions.conf).

        Returns:
            True if reload successful, False otherwise

        Raises:
            AsteriskError: If not connected to AMI
        """
        if not self._connected or not self.manager:
            raise AsteriskError("Not connected to AMI. Call connect() first.")

        try:
            response = await self.manager.send_action(
                {"Action": "Command", "Command": "dialplan reload"}
            )

            # Check response
            if hasattr(response, "success") and response.success:
                logger.info("Dialplan reloaded successfully")
                return True
            elif isinstance(response, dict) and response.get("Response") == "Success":
                logger.info("Dialplan reloaded successfully")
                return True
            else:
                logger.warning(f"Dialplan reload response: {response}")
                return False

        except Exception as e:
            logger.error(f"Dialplan reload failed: {e}")
            return False

    async def verify_endpoint(self, extension: str) -> bool:
        """Verify PJSIP endpoint exists.

        Args:
            extension: Extension number to check

        Returns:
            True if endpoint exists, False otherwise

        Raises:
            AsteriskError: If not connected to AMI
        """
        if not self._connected or not self.manager:
            raise AsteriskError("Not connected to AMI. Call connect() first.")

        try:
            response = await self.manager.send_action(
                {"Action": "PJSIPShowEndpoint", "Endpoint": extension}
            )

            # Check if endpoint exists
            if hasattr(response, "success") and response.success:
                return True
            elif isinstance(response, dict) and response.get("Response") == "Success":
                return True
            else:
                return False

        except Exception as e:
            logger.debug(f"Endpoint {extension} verification failed: {e}")
            return False

    async def execute_with_retry(self, operation: str, func, *args, **kwargs) -> bool:
        """Execute an AMI operation with retry logic.

        Args:
            operation: Description of operation for logging
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            True if operation successful, False otherwise
        """
        if not self.config.retry_on_failure:
            return await func(*args, **kwargs)

        for attempt in range(1, self.config.retry_max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                if result:
                    return True

                if attempt < self.config.retry_max_attempts:
                    logger.warning(
                        f"{operation} failed (attempt {attempt}/{self.config.retry_max_attempts}), "
                        f"retrying in {self.config.retry_delay_seconds}s..."
                    )
                    await asyncio.sleep(self.config.retry_delay_seconds)

            except Exception as e:
                logger.error(f"{operation} error (attempt {attempt}): {e}")
                if attempt < self.config.retry_max_attempts:
                    await asyncio.sleep(self.config.retry_delay_seconds)

        logger.error(f"{operation} failed after {self.config.retry_max_attempts} attempts")
        return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
