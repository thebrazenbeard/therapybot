"""Launch a private browser interface. No cloud calls, no subscription."""

import argparse
import os
import webbrowser
from pathlib import Path

from .server import create_server


def main():
    parser = argparse.ArgumentParser(description="TherapyBot experimental local interface")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--data", type=Path, default=Path.home() / ".therapybot" / "vault.sqlite3")
    parser.add_argument("--model-url", default=os.getenv("THERAPYBOT_MODEL_URL"),
                        help="Local KoboldCPP/llama.cpp HTTP origin, e.g. http://127.0.0.1:5001")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = create_server(args.data, args.model_url, args.port)
    address = f"http://127.0.0.1:{server.server_port}/#access={server.csrf_token}"
    print(f"TherapyBot 0.1 listening at http://127.0.0.1:{server.server_port}/")
    print("No model" if not server.model_url else f"Local model: {server.model_url}")
    print("Conversation and journal records are encrypted in the local vault; unlock through the page.")
    print("This is not a clinical service. Ctrl+C to stop and clear the in-memory key.")
    if args.no_browser:
        print(f"Private browser link (do not share or log): {address}")
    else:
        opened = webbrowser.open(address)
        if not opened:
            print("Could not open browser automatically. Restart with --no-browser to obtain a private link.")
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.vault.lock()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
