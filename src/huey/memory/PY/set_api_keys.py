# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Set Api Keys module (huey/memory/PY)

import json
import os

CONFIG_PATH = os.path.join("config", "pygpt_net", "config.json")

SERVICES = {
    "openai": "api_key",
    "google": "api_key_google",
    "deepseek": "api_key_deepseek",
}

ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_config(data):
    """Persist non-empty config values for local fallback use only."""
    cleaned = {k: v for k, v in data.items() if isinstance(v, str) and v.strip()}
    if not cleaned:
        print("No non-empty local keys to save; relying on environment variables.")
        return False

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(cleaned, fh, indent=2)

    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        print("Warning: Could not set restrictive permissions on local config file.")

    print("Warning: API key file is for local-only fallback and should remain gitignored.")
    return True


def prompt_service_choice():
    print("Select services to connect:")
    print("1) Auto - All")
    print("2) Manual - choose from OpenAI, Google, DeepSeek")
    choice = input("Enter choice [1/2]: ").strip()
    if choice == "1":
        return list(SERVICES.keys())
    selected = []
    for name in SERVICES:
        ans = input(f"Use {name.title()}? [y/N]: ").strip().lower()
        if ans == "y":
            selected.append(name)
    return selected


def prompt_keys(selected, data):
    for name in selected:
        key_name = SERVICES[name]
        env_name = ENV_VARS[name]
        env_value = os.environ.get(env_name, "").strip()

        if env_value:
            print(f"{name.title()} key detected in environment variable {env_name}; leaving unchanged.")
            continue

        if data.get(key_name, "").strip():
            print(f"{name.title()} key already present in local config fallback.")

        value = input(
            f"Enter {name.title()} API key (leave blank to keep env-only setup): "
        ).strip()
        if value:
            data[key_name] = value


def main():
    config = load_config()
    services = prompt_service_choice()
    if not services:
        print("No services selected.")
        return
    prompt_keys(services, config)
    wrote_file = save_config(config)
    if wrote_file:
        print("Local fallback keys saved to", CONFIG_PATH)
    print("Preferred setup: set API keys via environment variables or a local .env file.")


if __name__ == "__main__":
    main()
