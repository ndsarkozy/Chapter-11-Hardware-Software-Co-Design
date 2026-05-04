#!/usr/bin/env python3
"""
CECS 460 — Firmware Downloader

Pulls every Arduino sketch for Chapter 11 from the classroom server into
~/Documents/CECS460_Firmware/, then opens that folder.

Usage:
    python get_firmware.py
    python get_firmware.py --server 192.168.8.228:5000
"""

import argparse, json, os, sys, webbrowser
from urllib.request import urlopen, Request
from urllib.error import URLError

DEFAULT_SERVER = "192.168.8.228:5000"
DEST_DIR = os.path.join(os.path.expanduser("~"), "Documents", "CECS460_Firmware")


def fetch_manifest(server):
    url = f"http://{server}/firmware/sketches/"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8")).get("sketches", [])


def download(server, file_url, out_path):
    url = f"http://{server}{file_url}"
    with urlopen(url, timeout=30) as resp:
        data = resp.read()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    return len(data)


def open_folder(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        os.system(f'open "{path}"')
    else:
        os.system(f'xdg-open "{path}"')


def main():
    parser = argparse.ArgumentParser(description="CECS 460 Firmware Downloader")
    parser.add_argument("--server", default=DEFAULT_SERVER,
                        help=f"Server address (default: {DEFAULT_SERVER})")
    parser.add_argument("--dest", default=DEST_DIR,
                        help=f"Destination folder (default: {DEST_DIR})")
    args = parser.parse_args()

    print("=" * 60)
    print("  CECS 460 — Chapter 11 Firmware Downloader")
    print("=" * 60)
    print(f"Server: http://{args.server}")
    print(f"Destination: {args.dest}")
    print()

    try:
        sketches = fetch_manifest(args.server)
    except URLError as e:
        print(f"ERROR: Cannot reach server at {args.server}")
        print(f"       {e}")
        print()
        print("Check that you are connected to the classroom WiFi (DEEZ)")
        print("and that the server is running.")
        input("Press Enter to exit...")
        sys.exit(1)

    if not sketches:
        print("No firmware sketches available on the server.")
        input("Press Enter to exit...")
        sys.exit(1)

    total_files, total_bytes = 0, 0
    for sk in sketches:
        sketch_name = sk.get("sketch") or ""
        if sketch_name:
            print(f"[{sketch_name}]")
            sketch_dir = os.path.join(args.dest, sketch_name)
        else:
            sketch_dir = args.dest

        for f in sk["files"]:
            out_path = os.path.join(sketch_dir, f["name"])
            try:
                n = download(args.server, f["url"], out_path)
                total_files += 1
                total_bytes += n
                print(f"   downloaded  {f['name']:<30} {n//1024 or 1} KB")
            except Exception as e:
                print(f"   FAILED      {f['name']}: {e}")

    print()
    print("=" * 60)
    print(f"Done — {total_files} files, {total_bytes//1024} KB")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"  1. Open Arduino IDE")
    print(f"  2. File -> Open -> {args.dest}")
    print(f"     Pick the sketch your lab step needs (e.g. step1_baseline)")
    print(f"  3. Select board: ESP32 Dev Module")
    print(f"  4. Select your COM port and click Upload")
    print(f"  5. Return to your browser and start the lab")
    print()

    try:
        open_folder(args.dest)
    except Exception:
        pass

    print("Opening lesson page in your browser...")
    webbrowser.open(f"http://{args.server}/cecs460/login")
    print()
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
