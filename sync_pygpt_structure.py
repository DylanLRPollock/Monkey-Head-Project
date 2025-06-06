# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import os

PYGPT_DIR = os.path.join('repo', 'pygpt-MHP')
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def mirror(src, dst):
    if os.path.exists(dst):
        return False
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        placeholder = os.path.join(dst, 'README_PLACEHOLDER.md')
        with open(placeholder, 'w') as f:
            f.write(f'This directory mirrors `{src}` from the pygpt-MHP repo.')
    else:
        with open(dst, 'w') as f:
            f.write(f'Placeholder for `{src}` from the pygpt-MHP repo.')
    return True


def mirror_tree(src_root, dst_root, depth=1):
    for item in os.listdir(src_root):
        src_path = os.path.join(src_root, item)
        dst_path = os.path.join(dst_root, item)
        created = mirror(src_path, dst_path)
        if depth > 1 and os.path.isdir(src_path) and created:
            mirror_tree(src_path, dst_path, depth=depth-1)

if __name__ == "__main__":
    mirror_tree(PYGPT_DIR, ROOT_DIR, depth=2)

