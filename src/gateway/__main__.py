#!/usr/bin/env python3

if __name__ == "__main__":
    from src.gateway.api_server import app, init_monitor
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description="VPS Monitor API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--config", default="config/vps.json", help="Config file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    init_monitor(args.config)
    from src.log.logger import setup_logger
    logger = setup_logger("api_server")
    logger.info(f"Starting API server on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
