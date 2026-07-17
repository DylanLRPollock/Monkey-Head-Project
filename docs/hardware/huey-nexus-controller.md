# HueyNexusController

**Project:** Monkey-Head-Project  
**Status:** Maintained subproject direction  
**Supported reference family:** Google Nexus 5 and Google Nexus 7  
**Subproject codename:** Shark-themed name, unresolved  
**Review state:** Included in the v201.x human-oversight candidate

## Project position

**HueyNexusController** is a maintained subproject under the **Monkey-Head-Project** umbrella.

Its purpose is to restore and repurpose older Google Nexus hardware as dedicated physical control devices for Huey and Huey Body.

The controller is an authenticated operator interface. It does not replace Huey Brain, become an independent Huey identity, or hold canonical Huey memory.

## Fully supported reference hardware

The controller standard fully supports two device classes.

| Device | Codename | Controller class | Support status |
|---|---|---|---|
| Google Nexus 5 | `hammerhead` | Handset controller | Fully supported reference platform |
| Google Nexus 7 (2012 Wi-Fi) | `grouper` | Tablet controller | Fully supported reference platform |
| Google Nexus 7 (2012 cellular) | `tilapia` | Tablet controller | Fully supported reference platform |
| Google Nexus 7 (2013 Wi-Fi) | `flo` | Tablet controller | Fully supported reference platform |
| Google Nexus 7 (2013 cellular) | `deb` | Tablet controller | Fully supported reference platform |

### Nexus 5 role

The Nexus 5 remains the canonical handset-controller reference implementation. It is optimized for portable one-handed or pocketable Huey control.

### Nexus 7 role

The Nexus 7 is the canonical tablet-controller implementation. It is intended for:

- larger status and telemetry displays;
- more persistent room-side or workstation control;
- expanded touchscreen layouts;
- diagnostics and recovery surfaces;
- richer command history and alert presentation;
- optional docking or wall-mounted use.

Both Nexus 7 generations are supported. Device-specific installation images, kernels, recovery procedures, battery guidance, and hardware-support matrices must remain separate where the hardware differs.

## Hardware pool and replaceability

Initial deployment may begin with one working unit of either supported class.

The long-term pool may include multiple Nexus 5 and Nexus 7 units retained as:

- operational backups;
- development and testing devices;
- replacement controllers;
- sources of repair parts;
- known-good recovery devices.

The supported platform family is canonical, but each physical unit remains replaceable.

## Operating-system direction

### Primary target: native Debian

The primary target is a maintained Debian-based operating system that boots directly on supported Nexus hardware without Android as the host operating system.

No claim is made that full hardware support is already proven. Each device and variant must independently verify:

- boot and recovery;
- display and touchscreen;
- audio input and output;
- Wi-Fi and Bluetooth;
- USB and charging;
- battery telemetry;
- sensors and rotation;
- suspend and wake;
- thermal management;
- cellular data where applicable;
- cameras where required by the controller role.

### Fallback: LineageOS

LineageOS remains the fallback if native Debian cannot initially provide reliable hardware support.

The fallback must preserve the same controller protocol, authentication model, application boundary, provisioning process, and HIMS message contract wherever practical. The operating system should be replaceable without redesigning the controller architecture.

## Dedicated role

Nexus controller devices are dedicated Huey hardware rather than general-purpose personal phones or tablets.

Primary responsibilities include:

- controlling approved Huey Body functions;
- submitting touchscreen commands;
- submitting recorded or live voice commands;
- displaying Huey responses, alerts, status, and operational state;
- exposing approved movement, interaction, shutdown, and recovery controls;
- providing portable, docked, or room-side operator interfaces;
- preserving attributable command and response records.

A controller command is a request, not automatic authority to actuate hardware. Authentication, authorization, policy, safe-stop, and Body execution remain explicit downstream gates.

## Interface direction

### Preferred stack

- Phosh;
- GTK;
- Wayland;
- a purpose-built PyHuey or Huey controller application.

### Fallback stack

- KDE Plasma Mobile.

The interface must adapt to both supported form factors:

- **Nexus 5:** compact, touch-first, one-handed controller layout;
- **Nexus 7:** tablet-scale dashboard, diagnostics, history, and recovery layout.

The interface should not reproduce a complete desktop environment merely because one can be launched.

Minimum interface surfaces include:

- connection and authentication state;
- Huey and Body availability;
- command composition and confirmation;
- voice capture state;
- response and acknowledgement history;
- alerts and safe-state indicators;
- shutdown, recovery, and reconnect controls;
- controller identity, hardware class, and provisioning state.

## HIMS connection architecture

The controller family communicates through an authenticated connection to **HIMS - Huey Internal Messaging System**.

This subproject explicitly reactivates HIMS as the intended message pathway for bounded external controller clients.

The connection should support:

- controller registration and provisioning;
- device-class and hardware-variant identification;
- authenticated command submission;
- command acknowledgements;
- Huey responses;
- operational alerts;
- structured status messages;
- audit logging;
- reconnection and message-delivery tracking;
- revocation and replacement of lost or damaged devices.

HIMS remains transport and record infrastructure. Delivery does not itself grant execution or governance authority.

## Canonical and continuity boundaries

- Huey's identity does not reside on a controller.
- Canonical Huey memory remains elsewhere.
- Every controller is replaceable.
- Loss or damage of one device must not damage Huey's continuity.
- Another approved Nexus device may assume the role only after authentication and provisioning.
- Device-specific keys must be revocable.
- Controller state should be reconstructable from approved configuration and retained records.
- Personal phone or tablet data must not enter the controller image or Huey memory accidentally.

## Recycling objective

> Restore and repurpose phones and tablets more than ten years old as useful, maintainable Huey control devices.

The Nexus family is selected because it combines:

- personal and project significance;
- unlockable hardware;
- extensive custom-ROM history;
- available replacement units and parts;
- established repair and modification knowledge;
- sufficient performance for dedicated controller roles.

## Battery direction

Each battery must be evaluated for:

- remaining capacity;
- open-circuit and loaded voltage stability;
- charging behaviour;
- swelling or physical damage;
- temperature;
- discharge under sustained screen, Wi-Fi, cellular, and voice workloads;
- battery telemetry and cutoff behaviour.

Original batteries may be used temporarily only when safe.

Long-term options include:

- custom higher-capacity replacement batteries;
- externally supported battery modifications;
- purpose-built battery cases;
- docked power arrangements for stationary Nexus 7 deployments.

Any modification must preserve safe charging, temperature monitoring, cell protection, strain relief, physical protection, fire-risk mitigation, serviceability, and documented rollback.

## Initial success criteria

A complete proof for each supported device class demonstrates:

1. the device boots the selected operating system reliably;
2. the controller interface launches automatically;
3. the device authenticates with HIMS;
4. the user submits a touchscreen or voice command;
5. Huey receives and processes the command through approved boundaries;
6. the response and acknowledgement return to the controller;
7. the complete transaction is preserved in a structured log.

At least one Nexus 5 and one Nexus 7 implementation must independently pass the proof before the family can be called reproducibly supported.

## Validation stages

### Stage 0: intake and safety

- identify device, year, connectivity variant, and board revision;
- inspect enclosure, USB port, screen, buttons, cameras, and antennas;
- inspect and test battery;
- record bootloader and recovery state;
- preserve photographs and hardware notes.

### Stage 1: host operating system

- repeatable boot;
- stable display and touchscreen;
- Wi-Fi and USB networking;
- cellular networking where applicable;
- charging and battery telemetry;
- audio input and output;
- sensors and rotation;
- suspend, wake, thermal, and shutdown behaviour;
- recoverable installation image.

### Stage 2: controller application

- automatic launch;
- form-factor-appropriate interface;
- local settings and diagnostics;
- voice capture;
- offline-safe failure behaviour;
- signed or attributable build information.

### Stage 3: HIMS integration

- device provisioning;
- mutual authentication or an equivalently strong approved model;
- command-envelope validation;
- acknowledgements and responses;
- reconnect and delivery handling;
- logs without secret leakage;
- revocation and replacement testing.

### Stage 4: Huey Body control

- bounded test command;
- authorization check;
- operator confirmation where required;
- safe-stop and refusal path;
- observed physical result;
- complete attributable record.

## Recoverability and supported releases

A maintained controller release should include:

- installation documentation;
- checksums;
- recoverable images or reproducible build instructions;
- separate device/variant support matrices;
- provisioning and revocation procedures;
- backup-device onboarding procedures;
- parts and repair notes;
- battery and charging criteria;
- rollback instructions;
- supported-version and end-of-support policy.

## Long-term target

A reproducible maintained controller family with:

- full Nexus 5 handset support;
- full Nexus 7 tablet support;
- documented installations;
- recoverable system images;
- replaceable hardware;
- controlled updates;
- stable authenticated HIMS communication;
- screen and voice control;
- battery-upgrade documentation;
- support for physical Huey Body operation.

## Explicit non-claims

This document does not claim that:

- native Debian currently supports every component of every Nexus variant;
- all required installation images already exist;
- HIMS controller authentication is implemented;
- Body movement or shutdown authority has been granted;
- any battery modification is safe or complete;
- a controller is a Huey node;
- a controller carries Huey's identity or canonical memory;
- declaring Nexus 7 fully supported removes the need for variant-specific validation.

## Unresolved decisions

- shark-themed subproject codename;
- exact Debian base and kernel paths by device;
- boot chain, recovery, and image-building processes;
- Phosh versus Plasma Mobile acceptance evidence;
- controller application packaging and update path;
- voice capture and transcription placement;
- HIMS authentication and key-storage model;
- command authorization and confirmation rules;
- offline and degraded-operation behaviour;
- battery replacement or modification designs;
- supported release and end-of-support definitions.