#!/usr/bin/env python3
"""
ETL Manager — Entry point.

Usage:
    python main.py
    python main.py --host 0.0.0.0 --port 8000
    python main.py --reload  (development)
"""
import argparse
import uvicorn
from etl_app.config import settings
from etl_app.api.app import create_app

app = create_app()


def main():
    parser = argparse.ArgumentParser(description="ETL Manager Server")
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  ETL Manager v{settings.app_version}")
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  API: http://{args.host}:{args.port}/api/docs")
    print(f"{'='*50}\n")

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1 if args.reload else args.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main()
