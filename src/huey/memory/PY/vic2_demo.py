#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Vic2 Demo module (huey/memory/PY)

"""Simple VIC-II graphics demo for Raspberry Pi 3/4.

This script opens a 320x200 window using the classic Commodore 64
VIC-II color palette. It runs on any system with Pygame installed but
is optimized for the Raspberry Pi 3 and 4.
"""

import platform
import sys

import pygame

# 16-color palette matching the VIC-II chip
PALETTE = [
    (0x00, 0x00, 0x00),  # 0 Black
    (0xFF, 0xFF, 0xFF),  # 1 White
    (0x88, 0x00, 0x00),  # 2 Red
    (0xAA, 0xFF, 0xEE),  # 3 Cyan
    (0xCC, 0x44, 0xCC),  # 4 Purple
    (0x00, 0xCC, 0x55),  # 5 Green
    (0x00, 0x00, 0xAA),  # 6 Blue
    (0xEE, 0xEE, 0x77),  # 7 Yellow
    (0xDD, 0x88, 0x55),  # 8 Orange
    (0x66, 0x44, 0x00),  # 9 Brown
    (0xFF, 0x77, 0x77),  # 10 Light red
    (0x33, 0x33, 0x33),  # 11 Dark gray
    (0x77, 0x77, 0x77),  # 12 Medium gray
    (0xAA, 0xFF, 0x66),  # 13 Light green
    (0x00, 0x88, 0xFF),  # 14 Light blue
    (0xBB, 0xBB, 0xBB),  # 15 Light gray
]


def _check_raspberry_pi() -> None:
    """Warn when not running on a Raspberry Pi."""
    machine = platform.machine()
    if machine not in {"armv7l", "aarch64"}:
        print(
            "Warning: This demo is tuned for Raspberry Pi 3/4 but will run "
            "on other systems."
        )


def _draw_test_pattern(screen: pygame.Surface) -> None:
    """Fill the window with a simple color grid."""
    cell_w, cell_h = 20, 20
    idx = 0
    for y in range(0, 200, cell_h):
        for x in range(0, 320, cell_w):
            color = PALETTE[idx % len(PALETTE)]
            screen.fill(color, (x, y, cell_w, cell_h))
            idx += 1


def main() -> None:
    _check_raspberry_pi()
    pygame.init()
    screen = pygame.display.set_mode((320, 200))
    pygame.display.set_caption("VIC-II Demo")

    _draw_test_pattern(screen)
    font = pygame.font.SysFont("monospace", 20)
    txt = font.render("VIC-II Demo", True, PALETTE[1])
    screen.blit(txt, (90, 90))
    pygame.display.flip()

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
        clock.tick(60)


if __name__ == "__main__":
    main()
