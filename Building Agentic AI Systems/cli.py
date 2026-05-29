"""
cli.py
─────────────────────────────────────────────────────────────────────────────
AMA Health Agent — Command Line Interface

Run this file to start a conversation with the agent in your terminal.

Usage:
    python cli.py
    python cli.py --verbose      # show tool calls and results
    python cli.py --reset        # clear history between messages (stateless mode)

The agent maintains conversation history across turns within a session.
Type 'quit', 'exit', or press Ctrl+C to end the session.
─────────────────────────────────────────────────────────────────────────────
"""

import argparse
import sys
from dotenv import load_dotenv

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description="AMA Health Agent CLI")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print tool calls and results for each agent step",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset conversation history after each message (stateless mode)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum reasoning steps per message (default: 10)",
    )
    return parser.parse_args()


def print_banner():
    print("\n" + "=" * 60)
    print("  🏥  AMA — Community Health Triage Assistant (Ghana)")
    print("=" * 60)
    print("  Describe your symptoms or ask where to get care.")
    print("  Type 'quit' to exit | '--verbose' flag to see tool calls")
    print("=" * 60 + "\n")


def print_divider():
    print("\n" + "─" * 60 + "\n")


def main():
    args = parse_args()

    # Import here so missing dependencies give a clear error
    try:
        from agent.core import AmaAgent
    except ImportError as e:
        print(f"\n❌  Import error: {e}")
        print("    Have you completed the required exercises?")
        print("    Run: pip install -r requirements.txt\n")
        sys.exit(1)

    agent = AmaAgent(max_steps=args.max_steps, verbose=args.verbose)

    print_banner()

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in {"quit", "exit", "bye", "q"}:
                print("\nAMA: Take care and stay healthy! 🌿\n")
                break

            if user_input.lower() == "reset":
                agent.reset()
                print("\n[Conversation history cleared]\n")
                continue

            print_divider()
            print("AMA: ", end="", flush=True)

            try:
                response = agent.chat(user_input)
                print(response)
            except NotImplementedError as e:
                print(f"\n⚠️  Exercise not completed: {e}\n")
            except Exception as e:
                print(f"\n❌  Error: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()

            print_divider()

            if args.reset:
                agent.reset()

    except KeyboardInterrupt:
        print("\n\nAMA: Take care! 🌿\n")


if __name__ == "__main__":
    main()
