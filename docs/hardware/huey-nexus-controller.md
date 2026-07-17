# HueyNexusController

**Project:** Monkey-Head-Project  
**Status:** Maintained subproject direction  
**Reference platform:** Google Nexus 5 (`hammerhead`)  
**Subproject codename:** Shark-themed name, unresolved  
**Review state:** Included in the v201.x human-oversight candidate

## Project position

**HueyNexusController** is a maintained subproject under the **Monkey-Head-Project** umbrella.

Its purpose is to restore and repurpose Google Nexus 5 phones as dedicated physical control devices for Huey and Huey Body.

The handset is an authenticated controller and portable operator interface. It does not replace Huey Brain, become an independent Huey identity, or hold canonical Huey memory.

## Reference hardware

| Field | Specification |
|---|---|
| Device | Google Nexus 5 |
| Device codename | `hammerhead` |
| Subproject codename | Shark-themed name, to be selected |
| Initial deployment | One working handset |
| Long-term pool | Multiple Nexus 5 units for operational backup, development, testing, and replacement parts |
| Canonical role | First officially maintained Huey handset-controller reference implementation |

The Nexus 5 is canonical for this controller class, while each physical handset remains replaceable.

## Operating-system direction

### Primary target: native Debian

The primary target is a maintained Debian-based operating system that boots directly on Nexus 5 hardware without Android as the host operating system.

No claim is made that the complete hardware-support path is already proven. Display, touchscreen, audio, microphone, Wi-Fi, Bluetooth, USB, charging, battery telemetry, sensors, suspend, thermal management, and recovery must be verified independently.

### Fallback: LineageOS

LineageOS remains the fallback if native Debian cannot initially provide reliable hardware support.

The fallback should preserve the same Huey controller protocol and interface contract wherever practical. Application, authentication, message, and provisioning boundaries should not depend unnecessarily on the host operating system.

## Dedicated role

The Nexus 5 is dedicated Huey hardware rather than a general-purpose personal phone.

Primary responsibilities:

- control approved Huey Body functions;
- submit commands through the touchscreen;
- submit commands through recorded or live voice input;
- display Huey responses, alerts, status, and operational state;
- expose approved movement, interaction, shutdown, and recovery controls;
- provide a portable operator interface for Huey Body;
- preserve attributable command and response records.

A controller command is a request, not automatic authority to actuate hardware. Authentication, authorization, policy, safe-stop, and Body execution remain explicit downstream gates.

## Interface direction

### Preferred stack

- Phosh;
- GTK;
- Wayland;
- a purpose-built PyHuey or Huey controller application.

### Fallback stack

- KDE Plasma Mobile.

The interface must be designed for the Nexus 5 display and dedicated controller role. It should not reproduce a complete desktop environment merely because one can be launched.

Minimum interface surfaces should include:

- connection and authentication state;
- Huey and Body availability;
- command composition and confirmation;
- voice capture state;
- response and acknowledgement history;
- alerts and safe-state indicators;
- shutdown, recovery, and reconnect controls;
- controller identity and provisioning state.

## HIMS connection architecture

The controller will communicate through an authenticated connection to **HIMS - Huey Internal Messaging System**.

This subproject explicitly reactivates HIMS as the intended message pathway for a bounded external controller client.

The connection should support:

- controller registration and provisioning;
- authenticated command submission;
- command acknowledgements;
- Huey responses;
- operational alerts;
- structured status messages;
- audit logging;
- reconnection;
- message-delivery tracking;
- revocation and replacement of a lost handset.

HIMS remains transport and record infrastructure. Delivery does not itself grant execution or governance authority.

## Canonical and continuity boundaries

- Huey's identity does not reside on the handset.
- Canonical Huey memory remains elsewhere.
- The controller is replaceable.
- Loss or damage of one handset must not damage Huey's continuity.
- Another approved Nexus 5 should assume the role only after authentication and provisioning.
- Device-specific keys must be revocable.
- Controller state should be reconstructable from approved configuration and retained records.
- Personal phone data must not become part of the controller image or Huey memory by accident.

## Recycling objective

> Restore and repurpose phones more than ten years old as useful, maintainable Huey control devices.

The Nexus 5 is the first reference implementation because it combines:

- personal historical significance;
- existing repair and modification experience;
- unlockable hardware;
- extensive custom-ROM history;
- available replacement units and parts;
- sufficient performance for a dedicated controller role.

## Battery direction

Each battery must be evaluated for:

- remaining capacity;
- open-circuit and loaded voltage stability;
- charging behaviour;
- swelling or physical damage;
- temperature;
- discharge under sustained screen, Wi-Fi, and voice workloads;
- battery telemetry and cutoff behaviour.

Original batteries may be used temporarily only when safe.

Long-term options:

- custom higher-capacity replacement battery;
- externally supported battery modification;
- purpose-built battery case.

Any modification must preserve safe charging, temperature monitoring, cell protection, strain relief, physical protection, fire-risk mitigation, serviceability, and documented rollback.

## Initial success criterion

The first complete proof demonstrates:

1. the Nexus 5 boots the selected operating system reliably;
2. the controller interface launches automatically;
3. the device authenticates with HIMS;
4. the user submits a touchscreen or voice command;
5. Huey receives and processes the command through approved boundaries;
6. the response and acknowledgement return to the handset;
7. the complete transaction is preserved in a structured log.

## Validation stages

### Stage 0: intake and safety

- identify device and board revision;
- inspect enclosure, USB port, screen, buttons, cameras, and antennas;
- inspect and test battery;
- record bootloader and recovery state;
- preserve photographs and hardware notes.

### Stage 1: host operating system

- repeatable boot;
- stable display and touchscreen;
- Wi-Fi and USB networking;
- charging and battery telemetry;
- audio input/output;
- suspend, wake, thermal, and shutdown behaviour;
- recoverable installation image.

### Stage 2: controller application

- automatic launch;
- readable touch-first interface;
- local settings and diagnostics;
- voice capture;
- offline-safe failure behaviour;
- signed or attributable build information.

### Stage 3: HIMS integration

- device provisioning;
- mutual authentication or an equivalently strong approved model;
- command envelope validation;
- acknowledgements and responses;
- reconnect and delivery handling;
- logs without secret leakage;
- revocation and replacement test.

### Stage 4: Huey Body control

- bounded test command;
- authorization check;
- operator confirmation where required;
- safe-stop and refusal path;
- observed physical result;
- complete attributable record.

## Recoverability and hardware pool

A maintained controller release should include:

- installation documentation;
- checksums;
- recoverable system image or reproducible build instructions;
- provisioning and revocation procedure;
- backup-device onboarding procedure;
- parts and repair notes;
- known-good battery and charging criteria;
- rollback instructions;
- supported-version matrix.

## Long-term target

A reproducible and maintained Nexus 5 controller platform with:

- documented installation;
- recoverable system images;
- replaceable hardware;
- controlled updates;
- stable authenticated HIMS communication;
- screen and voice control;
- battery-upgrade documentation;
- support for physical Huey Body operation.

## Explicit non-claims

This document does not claim that:

- native Debian currently supports all Nexus 5 hardware;
- the primary interface stack has been selected through testing;
- HIMS controller authentication is implemented;
- Body movement or shutdown authority has been granted;
- any battery modification is safe or complete;
- the controller is a Huey node;
- the controller carries Huey's identity or canonical memory;
- one functioning handset proves a reproducible maintained platform.

## Unresolved decisions

- shark-themed subproject codename;
- exact Debian base and kernel path;
- boot chain, recovery, and image-building process;
- Phosh versus Plasma Mobile acceptance evidence;
- controller application packaging and update path;
- voice capture and transcription placement;
- HIMS authentication and key-storage model;
- command authorization and confirmation rules;
- offline and degraded-operation behaviour;
- battery replacement or modification design;
- long-term spare-device and parts inventory;
- definition of a supported controller release.
