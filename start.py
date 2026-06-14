"""
NeevDB v3.0.3 — One command starter
Run: python start.py
Run with custom DB: python start.py mydata.json
"""
import sys, os, time, webbrowser, threading

def check_deps():
    missing = []
    try: import fastapi
    except: missing.append("fastapi")
    try: import uvicorn
    except: missing.append("uvicorn")
    if missing:
        print(f"\n[NeevDB] Missing packages: {', '.join(missing)}")
        print(f"[NeevDB] Fix with: pip install neevdb[server]")
        print(f"         Or:       pip install {' '.join(missing)}\n")
        sys.exit(1)

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000")
    print("[NeevDB] Browser opened → http://localhost:8000\n")

def main():
    check_deps()
    import uvicorn

    db_path = sys.argv[1] if len(sys.argv) > 1 else "neevdb.json"
    os.environ["NEEVDB_PATH"] = db_path

    print("\n" + "=" * 52)
    print("  NeevDB v3.0.3 — Starting server...")
    print("=" * 52)
    print(f"  Database  : {db_path}")
    print(f"  Dashboard : http://localhost:8000")
    print(f"  API Docs  : http://localhost:8000/docs")
    print(f"  API Base  : http://localhost:8000/api")
    print(f"  Press Ctrl+C to stop")
    print("=" * 52 + "\n")

    threading.Thread(target=open_browser, daemon=True).start()

    # api.py is in the same folder as start.py
    api_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(api_dir)

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()