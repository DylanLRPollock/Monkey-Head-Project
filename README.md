# Monkey-Head-Project

<p align="center">
  <img src="src/huey/memory/PNG/HueyOS.png" alt="HueyOS - Monkey-Head-Project" width="80%">
</p>

<p align="center"><strong>Philosophy: "Breathing new life into old tech"</strong></p>

<p align="center">
  <a href="#project-definition">Definition</a> ·
  <a href="#v206-update">v206</a> ·
  <a href="#system-architecture">System Architecture</a> ·
  <a href="#huey-v4-embodiment">Huey V4</a> ·
  <a href="#node-first-architecture">Node-First</a> ·
  <a href="#hardware-specifications">Hardware</a> ·
  <a href="#labtech">LabTech</a> ·
  <a href="#pygpt-pyhuey--python-ecosystem">Runtime</a> ·
  <a href="#hims-huey-internal-messaging-system">HIMS</a> ·
  <a href="#documentation-layers">Documentation</a> ·
  <a href="#license-and-provenance">License</a>
</p>

<p align="center">
  <img alt="v206" src="https://img.shields.io/badge/release-Unified%20V206-5b2c83">
  <img alt="Status human review required" src="https://img.shields.io/badge/status-human%20review%20required-d97706">
  <img alt="Python 3.13" src="https://img.shields.io/badge/Python-3.13-3776ab">
  <img alt="Code GPLv3" src="https://img.shields.io/badge/code-GPLv3-2f855a">
</p>

> [!IMPORTANT]
> We have unified around V206 as Huey undergoes a critical transition into the V4 physical shell. This reassembly process is deliberate, focusing on integrating the new i9 architecture and updated cooling solutions while managing the structural weight and balance of the expanded internal array.

## Project Definition

The Monkey-Head-Project is the umbrella initiative for all subprojects and hardware developments supporting Huey, the modular AI-driven node. It encompasses the operating system, physical embodiments, controller logic, LabTech, research notes, and the future possibility of coordinating among multiple Huey nodes.

## V206 Update

The V206 update marks a major structural alignment, pivoting decisively toward the V4 physical shell. The focus is primarily on hardware integration, specifically housing the i9-12900K processor, managing the thermal load with robust air cooling, and strategically sourcing the high-VRAM arrays necessary for orchestration needs.

## System Architecture

The System Architecture is anchored by the V4 robotic shell, which physically houses the Intel i9-12900K processor on an ASUS TUF Gaming motherboard. Power is supplied by dual 1000W units configured for high-load stability. Storage is managed by an Intel Optane RAID 10 array for rapid OS execution, supported by large-capacity NAS drives for data redundancy. The integrated sound system combines Bose center speakers and generic side drivers with a marine-grade amplifier to complete the build.

## Huey V4 Embodiment

Huey V4 is the active, physical build currently in progress. It embodies the lab's ethos of breathing new life into old tech, utilizing robust salvaged materials. The physical structure is defined by a three-tiered architecture: the base is wooden and utilizes repurposed speaker enclosures and heavy-duty caster wheels, housing the internal sound system. The midsection is metal, featuring a modified Thermaltake Mozart chassis that houses the motherboard. The top section is primarily plastic and supports the Arduino-controlled 2005 WowWee animatronic monkey head.

## Node-First Architecture

A Huey node is designed as a physically individual AI unit with integrated local compute, brain, and body functions. Standalone operation is central to the architecture. While the long-term goal facilitates collective membership and shared infrastructure across multiple nodes, the initial deployment focuses fully on the viability of a single physical system.

## Hardware Specifications

The compute kernel is anchored by the Intel i9-12900K processor on an ASUS TUF Gaming Z790-Plus WiFi motherboard. Accelerated compute is delivered by four NVIDIA Tesla V100 32GB GPUs, providing 128GB of pooled VRAM for language model execution. Display output is handled by a fifth discrete graphics card, while power is secured by two 1000W PSUs for high-load stability.

Cooling is initially handled by a temporary traditional air heat sink, with a future upgrade path to liquid cooling once the external heat exchange is finalized.

Storage includes four Intel Optane M10 16GB drives in a RAID 10 array for OS execution, alongside two 10TB Western Digital NAS drives in a RAID 1 array for redundant, slower-access storage. All accelerator and graphics cards connect via PCIe extenders.

## LabTech

LabTech covers all external systems dedicated to the maintenance, development, and recovery of Huey. While these machines, such as the Lenovo Legion Go, interact with Huey for testing and architecture management, they remain strictly separate from the robot's primary compute kernel and operational identity.

## PyGPT (PyHuey) & Python Ecosystem

PyGPT (PyHuey) serves as the primary GUI and core runtime component for orchestrating large language model interactions. It is designed to provide a clear, observable operator surface while maintaining a resilient Command Line Interface path for system diagnostics, automation, and core hardware recovery.

The software architecture is unified around Python 3.13.x. The runtime environment includes backward compatibility support for Python 3.12, with active evaluation and testing underway for Python 3.14.

## HIMS (Huey Internal Messaging System)

HIMS serves as Huey's internal mail and communication service between sandboxed internal nodes. This system mandates end-to-end encryption to preserve secure, isolated channels across the distributed architecture.

## Documentation Layers

The project relies on three distinct documentation layers, each with a specific responsibility. The Master Plan outlines the machine-facing architecture, including status, reasoning, boundaries, and unresolved decisions. The README serves as the professional, human-oriented repository front door. Finally, dlrp.ca provides a public, cohesive explanation of the system with visible source status. These layers must remain synchronized while maintaining their distinct purposes.

## License and Provenance

The project code is licensed under GPL-3.0. However, other components of the project may be subject to varied licenses or specific conditions.

---

<p align="center"><strong>"Breathing new life into old tech"</strong></p>
