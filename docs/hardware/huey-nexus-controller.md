# HueyNexusController

**Project:** Monkey-Head-Project  
**Status:** Maintained subproject direction  
**Supported platforms:** Google Nexus 5 and Google Nexus 7 family  
**Subproject codename:** Shark-themed name, unresolved  
**Canon boundary:** Controller hardware only; not a Huey identity or Huey node

## Project position

**HueyNexusController** is a maintained subproject under the **Monkey-Head-Project** umbrella.

Its purpose is to restore and repurpose Google Nexus devices as dedicated physical control surfaces for Huey and Huey Body. The controller family includes both handset and tablet form factors:

- **Google Nexus 5** as the canonical handset controller;
- **Google Nexus 7** as a fully supported tablet controller.

Both platforms are first-class supported targets. Nexus 7 support is not experimental, secondary, or merely compatible: maintained controller releases must account for it alongside Nexus 5.

The controller is an authenticated operator interface. It does not replace Huey Brain, become an independent Huey identity, or hold canonical Huey memory.

## Supported hardware

| Platform | Variant / codename | Support position | Intended role |
|---|---|---|---|
| Google Nexus 5 | `hammerhead` | Fully supported canonical handset reference | Pocketable voice and touchscreen controller |
| Google Nexus 7 (2012 Wi-Fi) | `grouper` | Fully supported | Compact tablet controller and status display |
| Google Nexus 7 (2012 mobile) | `tilapia` | Fully supported | Mobile-connected tablet controller where hardware permits |
| Google Nexus 7 (2013 Wi-Fi) | `flo` | Fully supported | Preferred higher-resolution tablet controller |
| Google Nexus 7 (2013 LTE) | `deb` | Fully supported | LTE-capable tablet controller where hardware permits |

Each physical device remains replaceable. A maintained pool may contain operational controllers, development devices, recovery devices, and parts donors.

Platform-specific images, kernels, hardware profiles, battery procedures, and acceptance records may differ, but all supported Nexus 5 and Nexus 7 variants must preserve the same controller protocol and authority model.

## Form-factor roles

### Nexus 5 handset role

- pocketable portable control;
- one-handed status and acknowledgement use;
- recorded or live voice commands;
- emergency stop, shutdown, recovery, and reconnect controls;
- compact operator interface near Huey Body.

### Nexus 7 tablet role

- larger persistent status surface;
- expanded command, diagnostics, alert, and history views;
- tabletop, wall, dock, or service-console operation;
- richer PyHuey controller layouts;
- easier review of structured HIMS messages and logs;
- optional LTE operation on supported mobile variants.

The application may adapt its layout to the handset or tablet display, but both form factors remain protocol-compatible and equal members of the supported controller family.

## Operating-system direction

### Primary target: native Debian

The primary target is a maintained Debian-based operating system that boots directly on supported Nexus hardware without Android as the host operating system.

Native Debian support must be validated separately for each supported platform and variant. Required checks include:

- boot and recovery;
- display and touchscreen;
- Wi-Fi and, where fitted, cellular data;
- Bluetooth and USB;
- speakers and microphone;
- charging and battery telemetry;
- suspend, wake, shutdown, and thermal behaviour;
- cameras and sensors where assigned a controller role.

The project does not claim that native Debian hardware support is already complete.

### Fallback: LineageOS

LineageOS remains the supported fallback when native Debian cannot yet provide reliable hardware operation.

The fallback must preserve the controller application boundary, HIMS message contract, provisioning model, authority rules, logging, and replacement procedure wherever practical. Moving between Debian and LineageOS must not require redesigning the Huey controller protocol.

## Interface direction

### Preferred stack

- Phosh;
- GTK;
- Wayland;
- a purpose-built PyHuey or Huey controller application.

### Fallback stack

- KDE Plasma Mobile.

The interface must be touch-first and device-aware. It should not reproduce a complete desktop environment merely because one can be launched.

Minimum surfaces:

- connection and authentication state;
- registered controller identity;
- Huey and Body availability;
- command composition, review, and confirmation;
- recorded or live voice capture state;
- acknowledgements and response history;
- operational alerts and safe-state indicators;
- shutdown, recovery, revoke, and reconnect controls;
- local diagnostics and build/version information.

Tablet layouts may expose additional panels, history, logs, or persistent status views without granting broader authority than the handset interface.

## Dedicated role

Supported controllers may:

- submit approved commands through touchscreen input;
- submit recorded or live voice commands;
- display Huey responses, alerts, status, and operational state;
- expose approved movement, interaction, shutdown, and recovery requests;
- provide portable or docked Huey Body operator interfaces;
- preserve attributable command and response records.

A controller command is a request, not automatic authority to actuate hardware. Authentication, authorization, policy, confirmation, safe-stop, and Body execution remain explicit downstream gates.

## HIMS connection architecture

The controller family communicates through an authenticated connection to **HIMS — Huey Internal Messaging System**.

This subproject explicitly reactivates HIMS as the intended pathway for bounded external controller clients.

Required capabilities:

- controller registration and provisioning;
- device-specific authentication;
- authenticated command submission;
- command acknowledgements;
- Huey responses;
- operational alerts;
- structured status messages;
- audit logging;
- reconnection and delivery tracking;
- revocation and replacement of lost, damaged, or retired devices;
- platform and application version reporting.

HIMS remains transport and record infrastructure. Successful delivery does not itself grant execution or governance authority.

## Canonical and continuity boundaries

- Huey's identity does not reside on a Nexus controller.
- Canonical Huey memory remains elsewhere.
- Every controller is replaceable.
- Loss or damage of a device must not damage Huey's continuity.
- Another approved Nexus 5 or Nexus 7 may assume the role only after authentication and provisioning.
- Device-specific keys must be revocable.
- Controller state must be reconstructable from approved configuration and retained records.
- Personal phone or tablet data must not enter the controller image or Huey memory accidentally.
- Nexus 5 and Nexus 7 devices may share capabilities without becoming Huey nodes.

## Recycling objective

> Restore and repurpose phones and tablets more than ten years old as useful, maintainable Huey control devices.

The Nexus family is selected because it combines personal and technical significance, unlockable hardware, extensive custom-ROM history, repair knowledge, obtainable replacement devices and parts, and adequate performance for a dedicated controller role.

## Battery direction

Every battery must be evaluated for:

- remaining capacity;
- open-circuit and loaded voltage stability;
- charging behaviour;
- swelling or physical damage;
- temperature;
- discharge under sustained screen, Wi-Fi, voice, and status-display workloads;
- battery telemetry and cutoff behaviour.

Original batteries may be used temporarily only when safe.

Long-term options include:

- a high-quality replacement battery;
- a custom higher-capacity battery;
- an externally supported battery modification;
- a purpose-built battery case, dock, or fixed-power installation.

Any modification must preserve safe charging, temperature monitoring, cell protection, strain relief, physical protection, fire-risk mitigation, serviceability, and documented rollback. Nexus 5 and each Nexus 7 variant require separate physical and electrical battery records.

## Initial success criteria

### Shared controller proof

A complete proof demonstrates:

1. a supported Nexus device boots the selected operating system reliably;
2. the controller interface launches automatically;
3. the device authenticates with HIMS;
4. the user submits a touchscreen or voice command;
5. Huey receives and processes the request through approved boundaries;
6. the acknowledgement and response return to the device;
7. the complete transaction is preserved in a structured log.

### Platform acceptance

Full maintained support requires the shared proof on:

- at least one Nexus 5 `hammerhead`;
- at least one Nexus 7 tablet profile;
- documented repeatability or a recoverable image for each supported device class.

Individual variants may retain known limitations, but those limitations must be documented rather than silently removing the variant from supported status.

## Validation stages

### Stage 0 — intake and safety

- identify model, variant, board revision, and storage capacity;
- inspect enclosure, USB port, screen, buttons, cameras, antennas, and charging path;
- inspect and test the battery;
- record bootloader and recovery state;
- preserve photographs and hardware notes.

### Stage 1 — host operating system

- repeatable boot and recovery;
- stable display and touchscreen;
- Wi-Fi and USB networking;
- LTE or mobile data where fitted and approved;
- charging and battery telemetry;
- audio input/output;
- suspend, wake, thermal, and shutdown behaviour;
- recoverable installation image.

### Stage 2 — controller application

- automatic launch;
- handset- and tablet-appropriate layouts;
- local settings and diagnostics;
- voice capture;
- offline-safe failure behaviour;
- attributable build and version information.

### Stage 3 — HIMS integration

- device provisioning;
- mutual authentication or an equivalently strong approved model;
- command-envelope validation;
- acknowledgements and responses;
- reconnect and delivery handling;
- logs without secret leakage;
- revocation and replacement tests.

### Stage 4 — Huey Body control

- bounded test command;
- authorization check;
- operator confirmation where required;
- safe-stop and refusal path;
- observed physical result;
- complete attributable record.

### Stage 5 — multi-device continuity

- replace a Nexus 5 with another approved controller;
- replace or add a Nexus 7 without changing Huey's identity;
- revoke a lost device;
- preserve controller history and audit attribution;
- confirm handset and tablet commands use the same protocol and authority model.

## Recoverability and release requirements

A maintained controller release should include:

- installation documentation;
- per-platform support matrix;
- checksums;
- recoverable system images or reproducible build instructions;
- provisioning and revocation procedures;
- replacement-device onboarding;
- parts and repair notes;
- battery and charging criteria;
- rollback instructions;
- known limitations;
- supported application and protocol versions.

## Long-term target

A reproducible, maintained Nexus controller family with:

- fully supported Nexus 5 and Nexus 7 hardware classes;
- documented installation and recovery;
- replaceable devices;
- controlled updates;
- stable authenticated HIMS communication;
- handset and tablet layouts;
- screen and voice control;
- battery-upgrade documentation;
- support for physical Huey Body operation.

## Explicit non-claims

This document does not claim that:

- native Debian currently supports every Nexus 5 or Nexus 7 subsystem;
- every Nexus 7 variant has already passed validation;
- the primary interface stack has been selected through testing;
- HIMS controller authentication is implemented;
- Body movement or shutdown authority has been granted;
- any battery modification is safe or complete;
- a controller is a Huey node;
- a controller carries Huey's identity or canonical memory;
- one functioning device proves a reproducible maintained family.

## Unresolved decisions

- shark-themed subproject codename;
- exact Debian base, kernel, and boot path per platform;
- recovery and image-building process;
- Phosh versus Plasma Mobile acceptance evidence;
- controller application packaging and update path;
- handset versus tablet feature allocation;
- voice capture and transcription placement;
- HIMS authentication and key-storage model;
- command authorization and confirmation rules;
- offline and degraded-operation behaviour;
- battery replacement or modification design per model;
- long-term spare-device and parts inventory;
- exact supported-release and known-limitation policy.