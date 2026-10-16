"""CLI for an interview demo: no server or API key required."""
import argparse
import json
from .app import get_agent


def main():
    parser = argparse.ArgumentParser(description="TechIntel Agent CLI")
    parser.add_argument("query", help="research question")
    parser.add_argument("--mode", choices=["offline", "llm"], default="offline")
    parser.add_argument("--session", default="demo")
    args = parser.parse_args()
    result = get_agent().run(args.query, args.session, args.mode)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
