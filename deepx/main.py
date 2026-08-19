import sys
import os
import asyncio
from deepx.agent.runner import DeepCLIApp

def main():
    import argparse
    parser = argparse.ArgumentParser(description="DEEPX AGENT: Autonomous AI Engineering CLI")
    parser.add_argument("--headful", action="store_true", help="Launch browser in visible mode")
    parser.add_argument("--state", type=str, default=os.path.join(os.path.dirname(__file__), "core", "state.json"), help="Path to playwright state file")
    args = parser.parse_args()

    app = DeepCLIApp(state_file=args.state, headless=not args.headful)
    asyncio.run(app.run())

if __name__ == "__main__":
    main()
