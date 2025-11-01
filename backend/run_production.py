"""
Production server runner for the RAG API.
Runs with multiple workers and production-grade settings.
"""

import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    """Run the FastAPI application with production settings."""
    
    # Load production configuration from environment
    config = {
        "app": "main:app",
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8000")),
        "workers": int(os.getenv("API_WORKERS", "4")),
        "log_level": os.getenv("LOG_LEVEL", "info"),
        "access_log": True,
        "proxy_headers": True,
        "forwarded_allow_ips": "*",
    }
    
    print("="*60)
    print("Starting RAG API Server (Production Mode)")
    print("="*60)
    print(f"Host: {config['host']}")
    print(f"Port: {config['port']}")
    print(f"Workers: {config['workers']}")
    print(f"Log Level: {config['log_level']}")
    print("="*60)
    print(f"\nAPI Documentation: http://{config['host']}:{config['port']}/docs")
    print(f"Alternative Docs: http://{config['host']}:{config['port']}/redoc")
    print("\nPress CTRL+C to stop\n")
    
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
