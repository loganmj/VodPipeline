"""HTTP server for status endpoint."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from bin.state.job_state import JobStateManager
from bin.utils.logging_utils import log


class StatusHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the /status endpoint."""
    
    def log_message(self, format, *args):
        """Override to use our logging system."""
        log(f"[STATUS_SERVER] {format % args}")
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/status":
            self.handle_status()
        else:
            self.send_error(404, "Not Found")
    
    def handle_status(self):
        """Handle GET /status request."""
        try:
            state_manager = JobStateManager()
            state = state_manager.get_state()
            
            # If not running and not failed, return idle state
            if not state.is_running and state.stage != "Failed":
                response = {
                    "jobId": None,
                    "fileName": None,
                    "stage": "Idle",
                    "percent": 0,
                    "timestamp": state.last_updated_at.isoformat(),
                    "errorMessage": None
                }
            else:
                response = state.to_dict()
            
            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            log(f"[STATUS_SERVER] Error handling status request: {e}")
            self.send_error(500, "Internal Server Error")


class StatusServer:
    """
    HTTP server for exposing the /status endpoint.
    
    This server runs in a separate thread and provides non-blocking access
    to the current job state.
    """
    
    def __init__(self, port: int = 8080, host: str = "0.0.0.0"):
        """
        Initialize the status server.
        
        Args:
            port: Port number to listen on
            host: Host address to bind to
        """
        self.port = port
        self.host = host
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the HTTP server in a separate daemon thread."""
        if self.server is not None:
            log("[STATUS_SERVER] Server already running")
            return
        
        try:
            self.server = HTTPServer((self.host, self.port), StatusHandler)
            log(f"[STATUS_SERVER] Starting server on {self.host}:{self.port}")
            
            # Run server in a daemon thread so it doesn't block shutdown
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()
            
            log(f"[STATUS_SERVER] Server started successfully")
        except Exception as e:
            log(f"[STATUS_SERVER] Failed to start server: {e}")
            raise
    
    def _run_server(self):
        """Internal method to run the server loop."""
        try:
            self.server.serve_forever()
        except Exception as e:
            log(f"[STATUS_SERVER] Server error: {e}")
    
    def stop(self):
        """Stop the HTTP server."""
        if self.server is not None:
            log("[STATUS_SERVER] Stopping server")
            self.server.shutdown()
            self.server.server_close()  # Properly close the socket
            self.server = None
            if self.thread is not None:
                self.thread.join(timeout=5)
                self.thread = None
            log("[STATUS_SERVER] Server stopped")
