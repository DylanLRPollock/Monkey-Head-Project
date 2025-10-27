#!/usr/bin/env bash
set -euo pipefail

if [[ $(id -u) -ne 0 ]]; then
  echo "This script must be run as root." >&2
  exit 1
fi

suite="forky"

list_files=()
if [[ -f /etc/apt/sources.list ]]; then
  list_files+=("/etc/apt/sources.list")
fi
while IFS= read -r -d '' file; do
  list_files+=("$file")
done < <(find /etc/apt/sources.list.d -type f -name '*.list' -print0 2>/dev/null)

for file in "${list_files[@]}"; do
  if [[ ! -w $file ]]; then
    echo "Skipping $file (not writable)." >&2
    continue
  fi
  tmp_file="${file}.forky"
  cp "$file" "$tmp_file"
  sed -i -E "s/\b(buster|bullseye|bookworm|stable|testing)\b/${suite}/g" "$tmp_file"
  mv "$tmp_file" "$file"
  echo "Updated $file to use suite '${suite}'."
done

install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
  | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg

rm -f /etc/apt/sources.list.d/microsoft-edge.list \
  /etc/apt/sources.list.d/microsoft-edge-dev.list

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" \
  > /etc/apt/sources.list.d/microsoft-edge-beta.list

apt update
apt -y full-upgrade

