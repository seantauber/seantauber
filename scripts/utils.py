"""Utility functions for pipeline scripts."""

import subprocess
import atexit
import signal
import logging
import time
import os
from typing import Optional

logger = logging.getLogger(__name__)

class RedisServerManager:
    """Manages Redis server lifecycle."""
    
    def __init__(self):
        """Initialize Redis server manager."""
        self.redis_process: Optional[subprocess.Popen] = None
        # Register cleanup on script exit
        atexit.register(self.stop_server)
    
    def start_server(self) -> bool:
        """
        Start Redis server in the background.
        
        Returns:
            bool: True if server started successfully, False otherwise
        """
        if self.redis_process:
            logger.info("Redis server already running")
            return True
            
        try:
            # Start Redis server in the background
            self.redis_process = subprocess.Popen(
                ["redis-server", "--daemonize", "no"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if process is still running
            if self.redis_process.poll() is None:
                logger.info("Redis server started successfully")
                return True
            else:
                stdout, stderr = self.redis_process.communicate()
                logger.error(
                    f"Redis server failed to start: "
                    f"stdout={stdout.decode()}, stderr={stderr.decode()}"
                )
                self.redis_process = None
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Redis server: {str(e)}")
            self.redis_process = None
            return False
    
    def stop_server(self) -> None:
        """Stop Redis server if running."""
        if self.redis_process:
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(self.redis_process.pid), signal.SIGTERM)
                self.redis_process.wait(timeout=5)  # Wait up to 5 seconds
                logger.info("Redis server stopped")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                os.killpg(os.getpgid(self.redis_process.pid), signal.SIGKILL)
                logger.warning("Redis server force stopped")
            except Exception as e:
                logger.error(f"Error stopping Redis server: {str(e)}")
            finally:
                self.redis_process = None

# Global Redis server manager instance
redis_manager = RedisServerManager()

def ensure_redis_running() -> bool:
    """
    Ensure Redis server is running, starting it if needed.
    
    Returns:
        bool: True if Redis is running, False if it failed to start
    """
    return redis_manager.start_server()
