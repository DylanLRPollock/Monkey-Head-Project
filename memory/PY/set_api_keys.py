import json
import os

CONFIG_PATH = os.path.join("config", "pygpt_net", "config.json")

SERVICES = {
    "openai": "api_key",
    "google": "api_key_google",
    "deepseek": "api_key_deepseek",
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_config(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


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
        existing = data.get(key_name, "")
        prompt = (
            f"Enter {name.title()} API key"
            + (f" [current: {existing}]" if existing else "")
            + ": "
        )
        value = input(prompt).strip()
        if value:
            data[key_name] = value


def main():
    config = load_config()
    services = prompt_service_choice()
    if not services:
        print("No services selected.")
        return
    prompt_keys(services, config)
    save_config(config)
    print("API keys saved to", CONFIG_PATH)


if __name__ == "__main__":
    main()
