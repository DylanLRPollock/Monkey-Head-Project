package main

import (
    "encoding/json"
    "errors"
    "fmt"
    "os"
    "os/exec"
    "path/filepath"
    "runtime"
    "strings"
    "syscall"
    "time"
    "unsafe"
)

const appName = "HueyOS Launcher"
const version = "0.2.0"

type Config struct {
    Version          string `json:"version"`
    RepoPath         string `json:"repo_path"`
    PythonExecutable string `json:"python_executable"`
    FirstRunComplete bool   `json:"first_run_complete"`
    LastInstallUTC   string `json:"last_install_utc"`
}

func main() {
    args := os.Args[1:]
    if len(args) == 0 {
        if err := runDefault(); err != nil {
            messageBox(appName, err.Error(), 0x10)
            os.Exit(1)
        }
        return
    }

    cmd := strings.ToLower(args[0])
    switch cmd {
    case "--install", "install":
        if err := install(); err != nil {
            messageBox(appName, err.Error(), 0x10)
            os.Exit(1)
        }
        messageBox(appName, "HueyOS launcher folders and config were created.\n\nNext: run with --set-repo PATH to connect a Monkey-Head-Project checkout.", 0x40)
    case "--set-repo", "set-repo":
        if len(args) < 2 {
            messageBox(appName, "Missing repository path.\n\nUsage: HueyOS-Launcher.exe --set-repo L:\\Monkey-Head-Project", 0x10)
            os.Exit(1)
        }
        if err := setRepo(args[1]); err != nil {
            messageBox(appName, err.Error(), 0x10)
            os.Exit(1)
        }
        messageBox(appName, "Monkey-Head-Project path saved.\n\nDouble-click the launcher to start HueyOS Command Center when available.", 0x40)
    case "--set-python", "set-python":
        if len(args) < 2 {
            messageBox(appName, "Missing Python executable.\n\nUsage: HueyOS-Launcher.exe --set-python C:\\Path\\python.exe", 0x10)
            os.Exit(1)
        }
        if err := setPython(args[1]); err != nil {
            messageBox(appName, err.Error(), 0x10)
            os.Exit(1)
        }
        messageBox(appName, "Python executable saved.", 0x40)
    case "--launch", "launch":
        if err := launchCommandCenter(); err != nil {
            messageBox(appName, err.Error(), 0x10)
            os.Exit(1)
        }
    case "--doctor", "doctor":
        path, err := writeDoctorReport()
        if err != nil {
            messageBox(appName, err.Error(), 0x10)
            os.Exit(1)
        }
        _ = exec.Command("notepad.exe", path).Start()
    case "--open-config", "open-config":
        dir, err := configDir()
        if err != nil {
            messageBox(appName, err.Error(), 0x10)
            os.Exit(1)
        }
        _ = os.MkdirAll(dir, 0755)
        _ = exec.Command("explorer.exe", dir).Start()
    case "--help", "help", "/?":
        messageBox(appName, helpText(), 0x40)
    default:
        messageBox(appName, "Unknown option: "+args[0]+"\n\n"+helpText(), 0x10)
        os.Exit(1)
    }
}

func runDefault() error {
    if err := install(); err != nil {
        return err
    }
    cfg, err := loadConfig()
    if err != nil {
        return err
    }
    if strings.TrimSpace(cfg.RepoPath) == "" {
        dir, _ := configDir()
        _ = exec.Command("explorer.exe", dir).Start()
        return errors.New("HueyOS is installed, but no Monkey-Head-Project path is configured yet.\n\nRun:\nHueyOS-Launcher.exe --set-repo L:\\Monkey-Head-Project\n\nThe config folder has been opened.")
    }
    return launchCommandCenter()
}

func install() error {
    cdir, err := configDir()
    if err != nil { return err }
    ldir, err := localDir()
    if err != nil { return err }
    if err := os.MkdirAll(cdir, 0755); err != nil { return err }
    if err := os.MkdirAll(ldir, 0755); err != nil { return err }
    if err := os.MkdirAll(filepath.Join(ldir, "logs"), 0755); err != nil { return err }
    if err := os.MkdirAll(filepath.Join(ldir, "workspace"), 0755); err != nil { return err }
    cfgPath, err := configPath()
    if err != nil { return err }
    if _, err := os.Stat(cfgPath); os.IsNotExist(err) {
        cfg := Config{Version: version, PythonExecutable: "", FirstRunComplete: true, LastInstallUTC: time.Now().UTC().Format(time.RFC3339)}
        return saveConfig(cfg)
    }
    return nil
}

func setRepo(path string) error {
    if err := install(); err != nil { return err }
    abs, err := filepath.Abs(path)
    if err != nil { return err }
    info, err := os.Stat(abs)
    if err != nil { return fmt.Errorf("repository path does not exist: %s", abs) }
    if !info.IsDir() { return fmt.Errorf("repository path is not a directory: %s", abs) }
    if _, err := os.Stat(filepath.Join(abs, ".git")); err != nil {
        return fmt.Errorf("path does not look like a Git checkout: %s", abs)
    }
    cfg, _ := loadConfig()
    cfg.RepoPath = abs
    cfg.Version = version
    return saveConfig(cfg)
}

func setPython(path string) error {
    if err := install(); err != nil { return err }
    abs, err := filepath.Abs(path)
    if err != nil { return err }
    info, err := os.Stat(abs)
    if err != nil { return fmt.Errorf("python executable does not exist: %s", abs) }
    if info.IsDir() { return fmt.Errorf("python executable path is a directory: %s", abs) }
    cfg, _ := loadConfig()
    cfg.PythonExecutable = abs
    cfg.Version = version
    return saveConfig(cfg)
}

func launchCommandCenter() error {
    cfg, err := loadConfig()
    if err != nil { return err }
    if cfg.RepoPath == "" { return errors.New("Monkey-Head-Project path is not configured. Run --set-repo first.") }
    if _, err := os.Stat(cfg.RepoPath); err != nil { return fmt.Errorf("configured repo path is unavailable: %s", cfg.RepoPath) }

    py := cfg.PythonExecutable
    var command *exec.Cmd
    if py != "" {
        command = exec.Command(py, "-m", "huey.apps.command_center.cli", "--open")
    } else {
        command = exec.Command("py", "-3.13", "-m", "huey.apps.command_center.cli", "--open")
    }
    command.Dir = cfg.RepoPath
    if err := command.Start(); err != nil {
        // Fallback to python if py launcher is unavailable.
        fallback := exec.Command("python", "-m", "huey.apps.command_center.cli", "--open")
        fallback.Dir = cfg.RepoPath
        if ferr := fallback.Start(); ferr != nil {
            return fmt.Errorf("could not launch HueyOS Command Center. Primary error: %v. Fallback error: %v\n\nRun --doctor for details.", err, ferr)
        }
    }
    return nil
}

func writeDoctorReport() (string, error) {
    if err := install(); err != nil { return "", err }
    cfg, _ := loadConfig()
    ldir, err := localDir()
    if err != nil { return "", err }
    report := filepath.Join(ldir, "doctor-report.txt")
    var b strings.Builder
    b.WriteString(appName+" Doctor Report\r\n")
    b.WriteString("Version: "+version+"\r\n")
    b.WriteString("OS: "+runtime.GOOS+"/"+runtime.GOARCH+"\r\n")
    b.WriteString("Generated UTC: "+time.Now().UTC().Format(time.RFC3339)+"\r\n\r\n")
    b.WriteString("Config path: "+must(configPath())+"\r\n")
    b.WriteString("Local path: "+must(localDir())+"\r\n")
    b.WriteString("Repo path: "+cfg.RepoPath+"\r\n")
    b.WriteString("Python executable: "+cfg.PythonExecutable+"\r\n\r\n")
    b.WriteString(checkExecutable("py"))
    b.WriteString(checkExecutable("python"))
    b.WriteString(checkExecutable("git"))
    b.WriteString(checkExecutable("ffmpeg"))
    b.WriteString(checkExecutable("ffprobe"))
    if cfg.RepoPath != "" {
        b.WriteString("\r\nRepo checks:\r\n")
        b.WriteString(checkPath(filepath.Join(cfg.RepoPath, ".git"), ".git"))
        b.WriteString(checkPath(filepath.Join(cfg.RepoPath, "pyproject.toml"), "pyproject.toml"))
        b.WriteString(checkPath(filepath.Join(cfg.RepoPath, "scripts", "check_ffmpeg_environment.py"), "scripts/check_ffmpeg_environment.py"))
        b.WriteString(checkPath(filepath.Join(cfg.RepoPath, "scripts", "prepare_audio_for_transcription.py"), "scripts/prepare_audio_for_transcription.py"))
    }
    if err := os.WriteFile(report, []byte(b.String()), 0644); err != nil { return "", err }
    return report, nil
}

func checkExecutable(name string) string {
    path, err := exec.LookPath(name)
    if err != nil { return fmt.Sprintf("%s: NOT FOUND\r\n", name) }
    return fmt.Sprintf("%s: %s\r\n", name, path)
}

func checkPath(path, label string) string {
    if _, err := os.Stat(path); err != nil { return fmt.Sprintf("%s: missing\r\n", label) }
    return fmt.Sprintf("%s: present\r\n", label)
}

func helpText() string {
    return "HueyOS Launcher " + version + "\n\n" +
        "Double-click: launch Command Center if configured.\n\n" +
        "Commands:\n" +
        "  --install\n" +
        "  --set-repo PATH\n" +
        "  --set-python PATH_TO_PYTHON\n" +
        "  --launch\n" +
        "  --doctor\n" +
        "  --open-config\n" +
        "  --help\n\n" +
        "Safety: this launcher does not delete files, mutate Git repos, flash firmware, control hardware, or run arbitrary user commands."
}

func loadConfig() (Config, error) {
    cfgPath, err := configPath()
    if err != nil { return Config{}, err }
    data, err := os.ReadFile(cfgPath)
    if err != nil {
        return Config{Version: version}, nil
    }
    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil { return Config{}, err }
    if cfg.Version == "" { cfg.Version = version }
    return cfg, nil
}

func saveConfig(cfg Config) error {
    cfgPath, err := configPath()
    if err != nil { return err }
    if err := os.MkdirAll(filepath.Dir(cfgPath), 0755); err != nil { return err }
    data, err := json.MarshalIndent(cfg, "", "  ")
    if err != nil { return err }
    return os.WriteFile(cfgPath, data, 0644)
}

func configDir() (string, error) {
    base := os.Getenv("APPDATA")
    if base == "" {
        home, err := os.UserHomeDir()
        if err != nil { return "", err }
        base = filepath.Join(home, "AppData", "Roaming")
    }
    return filepath.Join(base, "HueyOS"), nil
}

func localDir() (string, error) {
    base := os.Getenv("LOCALAPPDATA")
    if base == "" {
        home, err := os.UserHomeDir()
        if err != nil { return "", err }
        base = filepath.Join(home, "AppData", "Local")
    }
    return filepath.Join(base, "HueyOS"), nil
}

func configPath() (string, error) {
    dir, err := configDir()
    if err != nil { return "", err }
    return filepath.Join(dir, "launcher.json"), nil
}

func must(s string, err error) string {
    if err != nil { return "<error: " + err.Error() + ">" }
    return s
}

func messageBox(title, text string, flags uintptr) {
    user32 := syscall.NewLazyDLL("user32.dll")
    proc := user32.NewProc("MessageBoxW")
    t, _ := syscall.UTF16PtrFromString(title)
    m, _ := syscall.UTF16PtrFromString(text)
    proc.Call(0, uintptr(unsafePointer(m)), uintptr(unsafePointer(t)), flags)
}

func unsafePointer(p *uint16) unsafe.Pointer { return unsafe.Pointer(p) }
