import os
import sys
import subprocess

def clear_screen():
    # Clear the screen for a cleaner UI
    os.system('cls' if os.name == 'nt' else 'clear')

def verify_python_installation():
    # Verify Python installation for GenCore requirements
    try:
        python_version = subprocess.check_output(["python", "--version"], text=True)
        print(f"[GenCore]: Python version: {python_version}")
        return True
    except subprocess.CalledProcessError:
        print("[GenCore]: Python is not installed or not in PATH.")
        return False

def full_setup():
    # Full setup process including environment setup and dependencies installation
    clear_screen()
    print("[GenCore]: Running full setup...")
    if not verify_python_installation():
        input("Press Enter to return to the menu...")
        return
    set_environment_variables()
    install_dependencies()
    print("[GenCore]: Full setup completed.")

def mini_setup():
    # Lightweight setup for GenCore
    clear_screen()
    print("[GenCore]: Running 'mini' setup...")
    subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run(["apt-get", "update"])
    subprocess.run(["apt-get", "install", "-y", "portaudio19-dev", "libasound2", "libasound2-dev"])
    subprocess.run(["python", "-m", "pip", "install", "python3.12-slim", "python3.12-venv"])
    print("[GenCore]: 'Mini' setup completed.")

def cleanup_files():
    # Cleanup temporary files and system cache
    clear_screen()
    print("[GenCore]: Cleaning up files...")
    # Example cleanup commands
    print("[GenCore]: System and application cache cleared.")
    print("[GenCore]: Cleanup completed.")

def launch_terminal():
    # Launch a new terminal window
    clear_screen()
    print("[GenCore]: Launching terminal...")
    os.system("start cmd" if os.name == 'nt' else "x-terminal-emulator")
    print("[GenCore]: Terminal launched.")

def update_python_debian():
    # Update Python packages and Debian system
    clear_screen()
    print("[GenCore]: Updating Python & Debian...")
    # Example Debian update commands
    print("[GenCore]: Python & Debian updated successfully.")

def create_build():
    # Compile and assemble resources for GenCore
    clear_screen()
    print("[GenCore]: Creating build...")
    # Example build command
    print("[GenCore]: Build created successfully.")

def create_volume():
    # Initialize and configure storage volumes for GenCore
    clear_screen()
    print("[GenCore]: Creating volume...")
    # Example Docker volume command
    print("[GenCore]: Volume created successfully.")

def create_container():
    # Deploy and start Docker containers for GenCore
    clear_screen()
    print("[GenCore]: Creating container...")
    # Example Docker container command
    print("[GenCore]: Container created and running.")

def kubernetes_setup():
    # Apply Kubernetes configurations and setup
    clear_screen()
    print("[GenCore]: Setting up Kubernetes...")
    # Example Kubernetes setup commands
    print("[GenCore]: Kubernetes setup completed successfully.")

def exit_program():
    # Exit the GenCore program
    clear_screen()
    print("[GenCore]: Thank you for using GenCore. Exiting now.")
    sys.exit()

def set_environment_variables():
    # Set environment variables for GenCore
    os.environ['PROJECT'] = 'GenCore'
    os.environ['ENVIRONMENT'] = 'Testing'
    print("[GenCore]: Environment variables set.")

def install_dependencies():
    # Install necessary dependencies for GenCore
    subprocess.run(["python", "-m", "pip", "install", "-r", "requirements.txt"])
    print("[GenCore]: Dependencies installed.")

menu_options = {
    '1': full_setup,
    '2': mini_setup,
    '3': cleanup_files,
    '4': launch_terminal,
    '5': update_python_debian,
    '6': create_build,
    '7': create_volume,
    '8': create_container,
    '9': kubernetes_setup,
    '10': exit_program
}

def main_menu():
    # Display the main menu and handle user input
    clear_screen()
    print("[****|     GenCore Management Console   |****]")
    print("[1] Full Setup")
    print("[2] 'Mini' Setup")
    print("[3] Cleanup Files")
    print("[4] Launch Terminal")
    print("[5] Update Python & Debian")
    print("[6] Create Build")
    print("[7] Create Volume")
    print("[8] Create Container")
    print("[9] Kubernetes Setup")
    print("[10] Exit Program")
    action = input("Select an option (1-10): ")
    if action in menu_options:
        menu_options[action]()
    else:
        print("Invalid Selection. Choose a valid option.")
        input("Press Enter to continue...")
        main_menu()

if __name__ == "__main__":
    main_menu()
