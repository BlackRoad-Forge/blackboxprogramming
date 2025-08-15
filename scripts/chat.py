#!/usr/bin/env python3
import os
import argparse
from ps_sha_infinity_client import PSSHAInfinityClient


def main():
    parser = argparse.ArgumentParser(description="Chat with PS-SHA Infinity API")
    parser.add_argument("--base-url", default=os.getenv("PS_SHA_BASE", "http://localhost:8000"))
    parser.add_argument("--token", default=os.getenv("PS_SHA_INFINITY_TOKEN"))
    args = parser.parse_args()

    client = PSSHAInfinityClient(base_url=args.base_url, token=args.token)

    print("Type messages to send to PS-SHA∞ API (Ctrl+C to exit).")
    msg_id = 0
    try:
        while True:
            message = input("You: ").strip()
            if not message:
                continue
            msg_id += 1
            idem_key = f"msg-{msg_id}"
            response = client.chat_bind(message, context={}, breath=0, idem_key=idem_key)
            print("Response:", response.get("echo"))
            print("Hash:", response.get("hash", {}).get("hash_hex"))
            print("Signature:", response.get("signature_hex"))
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    main()
