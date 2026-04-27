#!/usr/bin/env python3
"""
CECS Classroom — Student Device Connector v2

• Auto-detects ESP32 serial port
• Reads seat assignment from serial output
• Opens lesson page in browser automatically
• Can flash firmware from the classroom server (no Arduino IDE needed)

Requirements: Python 3.8+, pyserial (auto-installed)
Optional:     esptool (auto-installed when flashing)

Usage:  python student_client.py
        python student_client.py --server 192.168.8.10:5000
"""

import sys, os, re, threading, webbrowser, subprocess, time, json
from collections import deque
from urllib.request import urlopen, Request
from urllib.error import URLError

# ── Auto-install pyserial ─────────────────────────────────────────────────────
try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Installing pyserial...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial", "--quiet"])
    import serial
    import serial.tools.list_ports

import tkinter as tk
from tkinter import ttk, messagebox

# ── Configuration ─────────────────────────────────────────────────────────────
BAUD_RATE = 115200
POLL_MS   = 150
SCAN_MS   = 3000
DEFAULT_SERVER = "192.168.8.10:5000"
ESP_VIDS  = {0x10C4, 0x1A86, 0x303A, 0x0403}

# ── Regex patterns ────────────────────────────────────────────────────────────
RE_SEAT   = re.compile(r"Seat\s*:\s*(\d+)",            re.I)
RE_SLOT   = re.compile(r"Slot\s*:\s*(\d+)",            re.I)
RE_TOKEN  = re.compile(r"Token\s*:\s*([0-9a-fA-F]+)",  re.I)
RE_URL    = re.compile(r"URL\s*:\s*(https?://\S+)",    re.I)
RE_MAC    = re.compile(r"MAC:\s*([0-9A-Fa-f]{12})",    re.I)
RE_WIFI   = re.compile(r"\[WiFi\]\s*(Connected|Disconnected)", re.I)
RE_MQTT   = re.compile(r"\[MQTT\]\s*(Connected|Failed|Disconnected)", re.I)


class StudentClient:
    def __init__(self, root, server_addr=None):
        self.root = root
        self.root.title("CECS — Student Device Connector")
        self.root.configure(bg="#0d1117")
        self.root.minsize(680, 620)

        self.server = server_addr or DEFAULT_SERVER
        if not self.server.startswith("http"):
            self.server = f"http://{self.server}"

        # State
        self.ser = None
        self.running = False
        self.seat = None
        self.token = None
        self.url = None
        self.mac = None
        self.wifi_ok = False
        self.mqtt_ok = False
        self.url_opened = False
        self.flashing = False

        # Colors
        self.bg, self.card, self.border = "#0d1117", "#161b22", "#30363d"
        self.text, self.muted, self.accent = "#e6edf3", "#8b949e", "#58a6ff"
        self.green, self.red, self.yellow = "#3fb950", "#f85149", "#d29922"

        self._build_ui()
        self._scan_ports()
        self.root.after(SCAN_MS, self._periodic_scan)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=self.card, height=56)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="CECS Classroom", font=("Consolas", 11, "bold"),
                 fg=self.accent, bg=self.card).pack(side="left", padx=14)
        tk.Label(hdr, text="Student Device Connector", font=("Segoe UI", 10),
                 fg=self.muted, bg=self.card).pack(side="left", padx=4)

        # Status cards
        cards = tk.Frame(self.root, bg=self.bg)
        cards.pack(fill="x", padx=12, pady=(10,0))
        self.card_seat = self._status_card(cards, "SEAT", "--", self.accent)
        self.card_wifi = self._status_card(cards, "WiFi", "···", self.muted)
        self.card_mqtt = self._status_card(cards, "MQTT", "···", self.muted)
        self.card_mac  = self._status_card(cards, "MAC",  "···", self.muted)

        # Port selector + buttons
        pf = tk.Frame(self.root, bg=self.bg)
        pf.pack(fill="x", padx=12, pady=(10,0))

        tk.Label(pf, text="Port:", font=("Segoe UI", 9),
                 fg=self.muted, bg=self.bg).pack(side="left")
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(pf, textvariable=self.port_var,
                                        width=20, state="readonly")
        self.port_combo.pack(side="left", padx=(6,8))

        self.btn_connect = tk.Button(pf, text="Connect",
            font=("Segoe UI", 9, "bold"), fg="#fff", bg=self.accent,
            activebackground="#79c0ff", bd=0, padx=12, pady=4,
            cursor="hand2", command=self._toggle_connect)
        self.btn_connect.pack(side="left")

        self.btn_open = tk.Button(pf, text="Open Lesson Page",
            font=("Segoe UI", 9, "bold"), fg="#000", bg=self.green,
            activebackground="#56d364", bd=0, padx=12, pady=4,
            cursor="hand2", command=self._open_url, state="disabled")
        self.btn_open.pack(side="left", padx=(8,0))

        self.btn_flash = tk.Button(pf, text="Flash Firmware",
            font=("Segoe UI", 9, "bold"), fg="#000", bg=self.yellow,
            activebackground="#e8b931", bd=0, padx=12, pady=4,
            cursor="hand2", command=self._flash_firmware)
        self.btn_flash.pack(side="left", padx=(8,0))

        # URL display
        uf = tk.Frame(self.root, bg=self.bg)
        uf.pack(fill="x", padx=12, pady=(8,0))
        tk.Label(uf, text="Lesson URL:", font=("Segoe UI", 9),
                 fg=self.muted, bg=self.bg).pack(side="left")
        self.url_label = tk.Label(uf, text="Waiting for seat assignment...",
                                   font=("Consolas", 9), fg=self.yellow, bg=self.bg)
        self.url_label.pack(side="left", padx=(6,0), fill="x", expand=True)

        # Serial log
        lf = tk.Frame(self.root, bg=self.bg)
        lf.pack(fill="both", expand=True, padx=12, pady=(10,0))
        tk.Label(lf, text="Serial Output", font=("Segoe UI", 9, "bold"),
                 fg=self.muted, bg=self.bg).pack(anchor="w")
        self.log_text = tk.Text(lf, font=("Consolas", 9), bg="#010409", fg=self.text,
                                 bd=0, highlightthickness=1,
                                 highlightcolor=self.border, highlightbackground=self.border,
                                 insertbackground=self.text, wrap="word",
                                 state="disabled", padx=8, pady=6)
        self.log_text.pack(fill="both", expand=True, pady=(4,0))
        for tag, color in [("green", self.green), ("red", self.red),
                           ("yellow", self.yellow), ("blue", self.accent),
                           ("muted", self.muted)]:
            self.log_text.tag_configure(tag, foreground=color)

        # Command entry
        cf = tk.Frame(self.root, bg=self.card, height=36)
        cf.pack(fill="x", side="bottom"); cf.pack_propagate(False)
        tk.Label(cf, text="Send:", font=("Consolas", 9),
                 fg=self.muted, bg=self.card).pack(side="left", padx=(12,4))
        self.cmd_entry = tk.Entry(cf, font=("Consolas", 9), bg="#010409", fg=self.text,
                                   bd=0, insertbackground=self.text,
                                   highlightthickness=1, highlightcolor=self.border,
                                   highlightbackground=self.border)
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(0,8), pady=4)
        self.cmd_entry.bind("<Return>", self._send_command)

    def _status_card(self, parent, label, value, color):
        f = tk.Frame(parent, bg=self.card, bd=0, highlightthickness=1,
                     highlightbackground=self.border)
        f.pack(side="left", fill="x", expand=True, padx=(0,6))
        tk.Label(f, text=label, font=("Segoe UI", 8), fg=self.muted,
                 bg=self.card).pack(anchor="w", padx=10, pady=(6,0))
        lbl = tk.Label(f, text=value, font=("Consolas", 16, "bold"),
                        fg=color, bg=self.card)
        lbl.pack(anchor="w", padx=10, pady=(0,6))
        return lbl

    # ── Port scanning ─────────────────────────────────────────────────────────

    def _scan_ports(self):
        ports = serial.tools.list_ports.comports()
        esp = [p.device for p in ports if p.vid and p.vid in ESP_VIDS]
        other = [p.device for p in ports if p.device and p.device not in esp]
        all_p = esp + other
        self.port_combo["values"] = all_p
        if all_p and not self.port_var.get():
            self.port_var.set(all_p[0])
        if len(esp) == 1 and not self.running and not self.flashing:
            self.port_var.set(esp[0])
            self._toggle_connect()

    def _periodic_scan(self):
        if not self.running and not self.flashing:
            self._scan_ports()
        self.root.after(SCAN_MS, self._periodic_scan)

    # ── Connect / Disconnect ──────────────────────────────────────────────────

    def _toggle_connect(self):
        if self.running:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_var.get()
        if not port:
            self._log("No serial port selected", "red"); return
        try:
            self.ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
            self.running = True
            self.btn_connect.configure(text="Disconnect", bg=self.red)
            self._log(f"Connected to {port}", "green")
            self.root.after(POLL_MS, self._read_serial)
        except Exception as e:
            self._log(f"Failed to open {port}: {e}", "red")

    def _disconnect(self):
        self.running = False
        if self.ser:
            try: self.ser.close()
            except: pass
            self.ser = None
        self.btn_connect.configure(text="Connect", bg=self.accent)
        self._log("Disconnected", "yellow")

    # ── Serial reading ────────────────────────────────────────────────────────

    def _read_serial(self):
        if not self.running or not self.ser: return
        try:
            while self.ser.in_waiting:
                raw = self.ser.readline()
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if line: self._process_line(line)
        except serial.SerialException:
            self._log("Serial connection lost", "red")
            self._disconnect(); return
        except Exception as e:
            self._log(f"Read error: {e}", "red")
        if self.running:
            self.root.after(POLL_MS, self._read_serial)

    def _process_line(self, line):
        s = line.strip()
        if s.startswith('{"') or s == "." or all(c == '.' for c in s): return

        tag = self._classify(line)
        self._log(line, tag)

        m = RE_SEAT.search(line) or RE_SLOT.search(line)
        if m:
            self.seat = int(m.group(1))
            self.card_seat.configure(text=str(self.seat), fg=self.green)

        m = RE_TOKEN.search(line)
        if m: self.token = m.group(1)

        m = RE_URL.search(line)
        if m:
            self.url = m.group(1)
            self.url_label.configure(text=self.url, fg=self.green)
            self.btn_open.configure(state="normal")
            if not self.url_opened:
                self.url_opened = True
                self.root.after(500, self._open_url)

        m = RE_MAC.search(line)
        if m:
            self.mac = m.group(1)
            self.card_mac.configure(text=self.mac[-6:], fg=self.text)

        m = RE_WIFI.search(line)
        if m:
            ok = m.group(1).lower() == "connected"
            self.wifi_ok = ok
            self.card_wifi.configure(text="OK" if ok else "DOWN",
                                      fg=self.green if ok else self.red)

        m = RE_MQTT.search(line)
        if m:
            ok = m.group(1).lower() == "connected"
            self.mqtt_ok = ok
            self.card_mqtt.configure(text="OK" if ok else "DOWN",
                                      fg=self.green if ok else self.red)

    def _classify(self, line):
        if "SEAT ASSIGNED" in line or "SLOT ASSIGNED" in line: return "green"
        if RE_SEAT.search(line) or RE_SLOT.search(line): return "green"
        if RE_TOKEN.search(line): return "yellow"
        if "URL" in line: return "blue"
        if "[WiFi] Connected" in line or "[MQTT] Connected" in line: return "green"
        if "Disconnected" in line or "Failed" in line: return "red"
        if "SCORE:" in line: return "green"
        if any(c in line for c in "╔╠╚║"): return "blue"
        if "[Boot]" in line: return "muted"
        if "[Broadcast]" in line: return "yellow"
        return None

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, text, tag=None):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n", (tag,) if tag else ())
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 500:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", f"{lines-400}.0")
            self.log_text.configure(state="disabled")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _open_url(self):
        if self.url:
            self._log(f"Opening browser: {self.url}", "green")
            webbrowser.open(self.url)

    def _send_command(self, event=None):
        cmd = self.cmd_entry.get().strip()
        if not cmd or not self.ser or not self.running: return
        try:
            self.ser.write((cmd + "\n").encode("utf-8"))
            self._log(f"> {cmd}", "blue")
            self.cmd_entry.delete(0, "end")
        except Exception as e:
            self._log(f"Send error: {e}", "red")

    # ── Firmware Flashing ─────────────────────────────────────────────────────

    def _flash_firmware(self):
        """Download firmware from server and flash via esptool."""
        port = self.port_var.get()
        if not port:
            messagebox.showwarning("No Port", "Select a serial port first.")
            return

        # Disconnect serial if connected (esptool needs exclusive access)
        if self.running:
            self._disconnect()

        # Run in background thread
        self.flashing = True
        self.btn_flash.configure(state="disabled", text="Flashing...")
        t = threading.Thread(target=self._flash_thread, args=(port,), daemon=True)
        t.start()

    def _flash_thread(self, port):
        try:
            # 1. Query server for available firmware binaries
            self._log_safe("Checking server for firmware...", "blue")
            bins = self._fetch_firmware_list()
            if not bins:
                self._log_safe("No firmware binaries on server.", "red")
                self._log_safe("Ask your instructor to export compiled", "yellow")
                self._log_safe("binaries to firmware/bin/ on the server.", "yellow")
                return

            # Pick the first available (or let user choose if multiple)
            fw = bins[0]
            self._log_safe(f"Found: {fw['name']} ({fw['size']//1024} KB)", "green")

            # 2. Download the binary
            self._log_safe(f"Downloading {fw['name']}...", "blue")
            bin_path = self._download_firmware(fw)
            if not bin_path:
                self._log_safe("Download failed.", "red")
                return
            self._log_safe(f"Downloaded to {bin_path}", "green")

            # 3. Ensure esptool is installed
            self._log_safe("Checking esptool...", "blue")
            try:
                import esptool
            except ImportError:
                self._log_safe("Installing esptool (one-time)...", "yellow")
                subprocess.check_call([sys.executable, "-m", "pip", "install",
                                       "esptool", "--quiet"])
                import esptool

            # 4. Flash using esptool
            self._log_safe(f"Flashing {fw['name']} to {port}...", "yellow")
            self._log_safe("Hold BOOT button on ESP32 if needed.", "yellow")

            flash_args = [
                "--chip", "esp32",
                "--port", port,
                "--baud", "460800",
                "--before", "default_reset",
                "--after", "hard_reset",
                "write_flash",
                "-z",
                "--flash_mode", "dio",
                "--flash_size", "detect",
                "0x10000", bin_path,
            ]

            # esptool.main() expects sys.argv-style args
            try:
                esptool.main(flash_args)
                self._log_safe("", None)
                self._log_safe("═══════════════════════════════════", "green")
                self._log_safe("  FLASH COMPLETE — Rebooting ESP32", "green")
                self._log_safe("═══════════════════════════════════", "green")
                self._log_safe("", None)

                # Wait for reboot then auto-reconnect
                time.sleep(3)
                self.root.after(0, lambda: self._connect_after_flash(port))

            except SystemExit:
                # esptool calls sys.exit on completion
                self._log_safe("Flash completed.", "green")
                time.sleep(3)
                self.root.after(0, lambda: self._connect_after_flash(port))
            except Exception as e:
                self._log_safe(f"Flash error: {e}", "red")
                self._log_safe("Try holding the BOOT button and retry.", "yellow")

        except Exception as e:
            self._log_safe(f"Error: {e}", "red")
        finally:
            self.flashing = False
            self.root.after(0, lambda: self.btn_flash.configure(
                state="normal", text="Flash Firmware"))

    def _connect_after_flash(self, port):
        """Re-connect serial after flashing to read seat assignment."""
        self.port_var.set(port)
        self.url_opened = False  # Allow auto-open after fresh flash
        self._connect()

    def _fetch_firmware_list(self):
        """Query the classroom server for available .bin files."""
        try:
            url = f"{self.server}/firmware/bin/"
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("bins", [])
        except Exception as e:
            self._log_safe(f"Server unreachable: {e}", "red")
            return []

    def _download_firmware(self, fw_info):
        """Download a firmware binary to a temp location."""
        try:
            url = f"{self.server}{fw_info['url']}"
            tmp_dir = os.path.join(os.path.expanduser("~"), ".cecs_firmware")
            os.makedirs(tmp_dir, exist_ok=True)
            out_path = os.path.join(tmp_dir, fw_info["name"])
            with urlopen(url, timeout=30) as resp:
                data = resp.read()
                with open(out_path, "wb") as f:
                    f.write(data)
            return out_path
        except Exception as e:
            self._log_safe(f"Download error: {e}", "red")
            return None

    def _log_safe(self, text, tag):
        """Thread-safe logging."""
        self.root.after(0, lambda: self._log(text, tag))

    def _on_close(self):
        self.running = False
        if self.ser:
            try: self.ser.close()
            except: pass
        self.root.destroy()


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CECS Student Device Connector")
    parser.add_argument("--server", default=None,
                        help="Server address (e.g. 192.168.8.10:5000)")
    args = parser.parse_args()

    root = tk.Tk()
    try:
        import ctypes
        root.update()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
    except: pass

    app = StudentClient(root, server_addr=args.server)
    root.mainloop()
