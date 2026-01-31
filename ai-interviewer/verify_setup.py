import requests
import sys
import websocket
import threading
import time

def check_backend():
    try:
        r = requests.get("http://localhost:8000/health")
        if r.status_code == 200:
            print("[PASS] Backend Health Check")
        else:
            print(f"[FAIL] Backend Health Check: {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Backend Health Check: {e}")

def check_frontend():
    try:
        r = requests.get("http://localhost:5173")
        if r.status_code == 200:
            print("[PASS] Frontend Server Check")
        else:
            print(f"[FAIL] Frontend Server Check: {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Frontend Server Check: {e}")

def check_websocket():
    def on_open(ws):
        print("[PASS] WebSocket Connection Open")
        ws.close()

    def on_error(ws, error):
        print(f"[FAIL] WebSocket Error: {error}")

    ws = websocket.WebSocketApp("ws://localhost:8000/ws/stream/verify_script",
                                on_open=on_open,
                                on_error=on_error)
    ws.run_forever()

if __name__ == "__main__":
    print("Starting Verification...")
    check_backend()
    check_frontend()
    # Run WS check
    check_websocket()
