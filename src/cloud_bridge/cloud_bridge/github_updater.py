import os
import urllib.request


def load_env_file():
    paths_to_check = [".env", os.path.expanduser("~/ros2_ws_hedgehog/.env")]
    for path in paths_to_check:
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()
            break


def check_and_update_frontend():
    load_env_file()

    REPO_OWNER = "Pedgehog"
    REPO_NAME = "test_webpage_by_ai"
    BRANCH = "frontend-builds"

    TARGET_DIR = os.path.expanduser("~/ros2_ws_hedgehog/src/cloud_bridge/web")
    target_file = os.path.join(TARGET_DIR, "index.html")

    github_token = os.environ.get("GITHUB_TOKEN", "")

    raw_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/index.html"

    try:
        req = urllib.request.Request(raw_url)
        if github_token:
            req.add_header("Authorization", f"token {github_token}")

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                new_content = response.read()

                existing_content = b""
                if os.path.exists(target_file):
                    with open(target_file, "rb") as f:
                        existing_content = f.read()

                if new_content != existing_content:
                    os.makedirs(TARGET_DIR, exist_ok=True)
                    with open(target_file, "wb") as f:
                        f.write(new_content)
                    print(
                        "[INFO] [github_updater]: index.html erfolgreich aktualisiert."
                    )
                else:
                    print(
                        "[INFO] [github_updater]: Lokale index.html ist bereits auf dem neuesten Stand."
                    )
            else:
                print(
                    f"[WARN] [github_updater]: Konnte index.html nicht laden (Status: {response.status})"
                )

    except Exception as e:
        print(f"[WARN] [github_updater]: Update-Prüfung fehlgeschlagen: {e}")
