cat > hueyos-grub-default-install.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# HueyOS Clean GRUB Installer
# Target boot screen:
#
#                         HUEYOS
#
#
#                            4
#
# Black background, green text, hidden menu, quiet boot with errors visible.
#
# Target system family:
#   Debian / Ubuntu style GRUB using:
#   /etc/default/grub
#   /etc/grub.d/10_linux
#   /boot/grub
#   update-grub or grub-mkconfig

THEME_NAME="hueyos-clean"
THEME_DIR="/boot/grub/themes/${THEME_NAME}"
FONT_SRC="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_OUT="${THEME_DIR}/hueyos.pf2"

GRUB_FILE="/etc/default/grub"
GRUB_LINUX_FILE="/etc/grub.d/10_linux"
DROPIN_DIR="/etc/default/grub.d"
DROPIN_FILE="${DROPIN_DIR}/99_hueyos_clean.cfg"

TITLE_TEXT="${HUEYOS_TITLE_TEXT:-HUEYOS}"
TIMEOUT_SECONDS="${HUEYOS_TIMEOUT_SECONDS:-4}"
FONT_SIZE="${HUEYOS_FONT_SIZE:-24}"

GREEN="${HUEYOS_GREEN:-#00ff66}"
BLACK="${HUEYOS_BLACK:-#000000}"

GFXMODE="${HUEYOS_GFXMODE:-1024x768,800x600,640x480,auto}"

QUIET_ARGS='quiet loglevel=3 systemd.show_status=auto rd.systemd.show_status=auto udev.log_level=3 rd.udev.log_level=3 vt.global_cursor_default=0'

BACKUP_DIR="/root/hueyos-grub-default-backup-$(date +%Y%m%d-%H%M%S)"

info() {
  printf '[HueyOS GRUB] %s\n' "$*"
}

die() {
  printf '[HueyOS GRUB] ERROR: %s\n' "$*" >&2
  exit 1
}

have() {
  command -v "$1" >/dev/null 2>&1
}

require_root() {
  if [ "${EUID}" -ne 0 ]; then
    die "Run as root: sudo bash hueyos-grub-default-install.sh"
  fi
}

find_update_command() {
  if have update-grub; then
    printf '%s\n' "update-grub"
  elif have grub-mkconfig; then
    printf '%s\n' "grub-mkconfig -o /boot/grub/grub.cfg"
  elif have grub2-mkconfig; then
    printf '%s\n' "grub2-mkconfig -o /boot/grub/grub.cfg"
  else
    return 1
  fi
}

install_requirements() {
  local missing=()

  have grub-mkfont || missing+=(grub-common)

  if [ ! -f "${FONT_SRC}" ]; then
    missing+=(fonts-dejavu-core)
  fi

  if [ "${#missing[@]}" -gt 0 ]; then
    have apt-get || die "Missing packages and apt-get is unavailable: ${missing[*]}"
    info "Installing required packages: ${missing[*]}"
    apt-get update
    apt-get install -y "${missing[@]}"
  fi

  have grub-mkfont || die "grub-mkfont is still unavailable"
  [ -f "${FONT_SRC}" ] || die "Font source missing: ${FONT_SRC}"
}

backup_current_state() {
  info "Creating backup at ${BACKUP_DIR}"
  mkdir -p "${BACKUP_DIR}"

  [ -f "${GRUB_FILE}" ] && cp -a "${GRUB_FILE}" "${BACKUP_DIR}/etc-default-grub"
  [ -d "${DROPIN_DIR}" ] && cp -a "${DROPIN_DIR}" "${BACKUP_DIR}/etc-default-grub.d"
  [ -f "${GRUB_LINUX_FILE}" ] && cp -a "${GRUB_LINUX_FILE}" "${BACKUP_DIR}/10_linux"
  [ -f /boot/grub/grub.cfg ] && cp -a /boot/grub/grub.cfg "${BACKUP_DIR}/grub.cfg"
  [ -d "${THEME_DIR}" ] && cp -a "${THEME_DIR}" "${BACKUP_DIR}/theme-existing"
}

remove_old_hueyos_dropins() {
  info "Removing old HueyOS GRUB drop-ins"

  mkdir -p "${DROPIN_DIR}"

  rm -f "${DROPIN_DIR}"/*huey*.cfg 2>/dev/null || true
  rm -f "${DROPIN_DIR}"/*Huey*.cfg 2>/dev/null || true
  rm -f "${DROPIN_DIR}"/99_hueyos_clean.cfg 2>/dev/null || true
}

clean_grub_key_from_file() {
  local file="$1"
  local key="$2"

  [ -f "${file}" ] || return 0

  sed -i -E "/^[[:space:]]*#?[[:space:]]*${key}=.*/d" "${file}"
}

clean_active_grub_settings() {
  info "Cleaning conflicting GRUB settings from ${GRUB_FILE}"

  local keys=(
    GRUB_DEFAULT
    GRUB_TIMEOUT_STYLE
    GRUB_TIMEOUT
    GRUB_TERMINAL
    GRUB_TERMINAL_OUTPUT
    GRUB_GFXMODE
    GRUB_GFXPAYLOAD_LINUX
    GRUB_FONT
    GRUB_THEME
    GRUB_BACKGROUND
    GRUB_HIDDEN_TIMEOUT
    GRUB_HIDDEN_TIMEOUT_QUIET
    GRUB_CMDLINE_LINUX_DEFAULT
  )

  local key
  for key in "${keys[@]}"; do
    clean_grub_key_from_file "${GRUB_FILE}" "${key}"
  done
}

build_grub_font() {
  info "Building safe GRUB font: ${FONT_SIZE}px"

  mkdir -p "${THEME_DIR}"

  local font_log
  font_log="$(grub-mkfont \
    --verbose \
    --range=0x20-0x7E \
    --size="${FONT_SIZE}" \
    --name="HueyOS" \
    --output="${FONT_OUT}" \
    "${FONT_SRC}" 2>&1)"

  printf '%s\n' "${font_log}" > "${THEME_DIR}/hueyos-font.log"

  [ -s "${FONT_OUT}" ] || die "GRUB font was not created: ${FONT_OUT}"

  local font_name
  font_name="$(printf '%s\n' "${font_log}" | awk -F': ' '/[Ff]ont [Nn]ame/ {print $2; exit}' | sed 's/[[:space:]]*$//')"

  if [ -z "${font_name}" ]; then
    font_name="HueyOS Regular ${FONT_SIZE}"
  fi

  printf '%s\n' "${font_name}"
}

write_theme() {
  local font_name="$1"

  info "Writing clean HueyOS GRUB theme"

  mkdir -p "${THEME_DIR}"

  cat > "${THEME_DIR}/theme.txt" <<THEME
# HueyOS Clean GRUB Theme
# Black background, green centered title, green centered countdown.
# The boot menu exists underneath but is visually hidden during normal boot.

desktop-color: "${BLACK}"
title-text: ""
title-color: "${GREEN}"
message-color: "${GREEN}"
message-bg-color: "${BLACK}"

+ label {
  left = 0
  top = 30%
  width = 100%
  height = 60
  text = "${TITLE_TEXT}"
  font = "${font_name}"
  color = "${GREEN}"
  align = "center"
}

+ label {
  id = "__timeout__"
  left = 0
  top = 48%
  width = 100%
  height = 60
  font = "${font_name}"
  color = "${GREEN}"
  align = "center"
}

+ boot_menu {
  left = 0
  top = 80%
  width = 100%
  height = 1

  item_font = "${font_name}"
  selected_item_font = "${font_name}"

  item_color = "${BLACK}"
  selected_item_color = "${BLACK}"

  item_height = 1
  item_padding = 0
  item_spacing = 0

  icon_width = 0
  icon_height = 0
  item_icon_space = 0
}
THEME
}

write_grub_settings_to_default_file() {
  info "Writing HueyOS settings to ${GRUB_FILE}"

  cat >> "${GRUB_FILE}" <<GRUBCFG

# --- HueyOS clean GRUB boot screen ---
GRUB_DEFAULT=0
GRUB_TIMEOUT_STYLE=menu
GRUB_TIMEOUT=${TIMEOUT_SECONDS}
GRUB_TERMINAL_OUTPUT="gfxterm"
GRUB_GFXMODE="${GFXMODE}"
GRUB_GFXPAYLOAD_LINUX=keep
GRUB_FONT="${FONT_OUT}"
GRUB_THEME="${THEME_DIR}/theme.txt"
GRUB_CMDLINE_LINUX_DEFAULT="${QUIET_ARGS}"
GRUBCFG
}

write_grub_settings_dropin() {
  info "Writing final HueyOS override drop-in: ${DROPIN_FILE}"

  mkdir -p "${DROPIN_DIR}"

  cat > "${DROPIN_FILE}" <<GRUBCFG
# HueyOS clean GRUB boot screen
# This drop-in ensures HueyOS settings win on systems that source /etc/default/grub.d/*.cfg.

GRUB_DEFAULT=0
GRUB_TIMEOUT_STYLE=menu
GRUB_TIMEOUT=${TIMEOUT_SECONDS}
GRUB_TERMINAL_OUTPUT="gfxterm"
GRUB_GFXMODE="${GFXMODE}"
GRUB_GFXPAYLOAD_LINUX=keep
GRUB_FONT="${FONT_OUT}"
GRUB_THEME="${THEME_DIR}/theme.txt"
GRUB_CMDLINE_LINUX_DEFAULT="${QUIET_ARGS}"
GRUBCFG
}

patch_10_linux_silent_loading_messages() {
  if [ ! -f "${GRUB_LINUX_FILE}" ]; then
    info "Skipping kernel loading-message patch; ${GRUB_LINUX_FILE} not found"
    return 0
  fi

  info "Suppressing GRUB 'Loading Linux' and 'Loading initial ramdisk' lines"

  python3 <<'PY'
from pathlib import Path

path = Path("/etc/grub.d/10_linux")
text = path.read_text()

new_lines = []
for line in text.splitlines():
    # Debian/GRUB emits visible bootloader messages through lines like:
    # echo '$(echo "$message" | grub_quote)'
    # Removing these does not remove kernel/initrd boot commands.
    if 'echo "$message" | grub_quote' in line:
        continue
    new_lines.append(line)

path.write_text("\n".join(new_lines) + "\n")
PY

  chmod +x "${GRUB_LINUX_FILE}"
}

write_restore_helper() {
  local restore="/usr/local/sbin/hueyos-grub-restore"

  info "Writing restore helper: ${restore}"

  cat > "${restore}" <<'RESTORE'
#!/usr/bin/env bash
set -euo pipefail

info() {
  printf '[HueyOS GRUB Restore] %s\n' "$*"
}

die() {
  printf '[HueyOS GRUB Restore] ERROR: %s\n' "$*" >&2
  exit 1
}

if [ "${EUID}" -ne 0 ]; then
  die "Run as root: sudo hueyos-grub-restore"
fi

latest_backup="$(ls -1dt /root/hueyos-grub-default-backup-* 2>/dev/null | head -n 1 || true)"

if [ -z "${latest_backup}" ]; then
  die "No HueyOS GRUB backup found under /root"
fi

info "Restoring from ${latest_backup}"

if [ -f "${latest_backup}/etc-default-grub" ]; then
  cp -a "${latest_backup}/etc-default-grub" /etc/default/grub
else
  die "Backup is missing /etc/default/grub"
fi

rm -rf /etc/default/grub.d
if [ -d "${latest_backup}/etc-default-grub.d" ]; then
  cp -a "${latest_backup}/etc-default-grub.d" /etc/default/grub.d
else
  mkdir -p /etc/default/grub.d
fi

if [ -f "${latest_backup}/10_linux" ]; then
  cp -a "${latest_backup}/10_linux" /etc/grub.d/10_linux
  chmod +x /etc/grub.d/10_linux
fi

rm -rf /boot/grub/themes/hueyos-clean

if command -v update-grub >/dev/null 2>&1; then
  update-grub
elif command -v grub-mkconfig >/dev/null 2>&1; then
  grub-mkconfig -o /boot/grub/grub.cfg
elif command -v grub2-mkconfig >/dev/null 2>&1; then
  grub2-mkconfig -o /boot/grub/grub.cfg
else
  die "Could not find update-grub, grub-mkconfig, or grub2-mkconfig"
fi

info "Restore complete. Reboot to verify."
RESTORE

  chmod 0755 "${restore}"
}

regenerate_grub() {
  local update_cmd
  update_cmd="$(find_update_command)" || die "Could not find update-grub, grub-mkconfig, or grub2-mkconfig"

  info "Regenerating GRUB with: ${update_cmd}"

  # Intentional word splitting for command plus arguments.
  # shellcheck disable=SC2086
  ${update_cmd}
}

verify_result() {
  info "Verifying generated GRUB config"

  if [ -f /boot/grub/grub.cfg ] && grep -q "${THEME_DIR}/theme.txt" /boot/grub/grub.cfg; then
    info "Theme reference found in /boot/grub/grub.cfg"
  else
    info "WARNING: Theme reference was not found in /boot/grub/grub.cfg"
  fi

  if [ -f /boot/grub/grub.cfg ] && grep -q "loglevel=3" /boot/grub/grub.cfg; then
    info "Quiet/error kernel args found in /boot/grub/grub.cfg"
  else
    info "WARNING: Quiet/error kernel args were not found in /boot/grub/grub.cfg"
  fi
}

main() {
  require_root

  [ -d /boot/grub ] || die "/boot/grub not found"
  [ -f "${GRUB_FILE}" ] || die "${GRUB_FILE} not found"

  install_requirements
  backup_current_state
  remove_old_hueyos_dropins
  clean_active_grub_settings

  rm -rf "${THEME_DIR}"

  local font_name
  font_name="$(build_grub_font)"

  info "Using GRUB font name: ${font_name}"

  write_theme "${font_name}"
  write_grub_settings_to_default_file
  write_grub_settings_dropin
  patch_10_linux_silent_loading_messages
  write_restore_helper
  regenerate_grub
  verify_result

  cat <<DONE

Done.

Expected normal boot flow:

                         ${TITLE_TEXT}


                            ${TIMEOUT_SECONDS}

Then boot continues quietly.

Visible behavior:
  - Black background
  - Green HueyOS title
  - Green countdown
  - No visible Debian/GRUB menu
  - No visible kernel version loading line
  - Normal boot chatter hidden
  - Errors still allowed to appear

Restore command:
  sudo hueyos-grub-restore

Backup directory:
  ${BACKUP_DIR}

Reboot when ready:
  sudo reboot

DONE
}

main "$@"
EOF

chmod +x hueyos-grub-default-install.sh
