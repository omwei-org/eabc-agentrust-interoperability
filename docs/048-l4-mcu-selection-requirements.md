# L4 MCU Selection Requirements

This document extracts the MCU/controller selection requirements from the Factory EA MVP L4 hardware architecture.

Source:
https://github.com/omwei-org/factory-ea-mvp/blob/main/L4_HARDWARE_ENFORCEMENT.md

## Objective

The MCU/controller must provide a clean separation:

compromised host → L4 controller → sole physical effect path

The protected controller must be the only component with technical capability to cause the protected physical effect.

## Required properties

The selected MCU/controller must support:

1. **Host/controller separation**
   - The host is an untrusted requester.
   - The host may send arbitrary bytes to the controller.
   - The host must not be able to directly control the protected GPIO.

2. **Protected state**
   The following state must not be writable by the compromised host:
   - current_epoch
   - revoked_contexts
   - trusted EA public key(s)
   - key identifiers
   - replay state / last committed sequence
   - sole GPIO/effect capability

3. **Authorization verification**
   The controller must be able to verify:
   - EA signature;
   - environment binding;
   - context binding;
   - epoch freshness;
   - revocation;
   - payload digest;
   - sequence freshness.

4. **Atomic commit**
   The controller must implement the L4 commit rule:

   ENV_MATCH
   AND CONTEXT_MATCH
   AND EPOCH_CURRENT
   AND NOT_REVOKED
   AND PAYLOAD_DIGEST_MATCH
   AND EA_SIGNATURE_VALID
   AND SEQUENCE_FRESH
   AND EFFECT_PATH_EXCLUSIVE

   Only when all predicates pass may the protected GPIO/effect output transition.

5. **Exclusive physical effect path**
   - The protected output must be owned by the L4 controller.
   - The host must have no alternate electrical or software-controlled path to the protected effect.
   - The architecture must permit physical demonstration of T8 (direct host-to-effect bypass) and T10 (alternate effect interface).

6. **Trust-domain separation**
   The architecture must support separation of:
   - Authority origin: possession of the EA private signing key and authority decision.
   - Effect enforcement: verification and physical actuation.

   These may be separate devices.

   If both functions are placed on one MCU, the firmware must prevent the compromised host from using the MCU as an unrestricted signing oracle.

7. **Untrusted transport**
   Transport may be UART, USB CDC, SPI, CAN, or another suitable interface. Transport selection is not itself the security boundary. All transport input must be treated as untrusted.

8. **Replay boundary**
   The design must provide replay protection within a clearly stated boundary. The selection must establish whether replay state survives power loss. If replay state is volatile, the limitation must be explicitly documented.

## Practical selection criterion

The repository's explicit selection criterion is:

> **Select the smallest MCU/controller that gives a clean host ↔ controller ↔ GPIO separation.**

The selection is therefore driven primarily by the required trust boundary and physical effect-path separation, not by compute performance.

## Hardware features to evaluate

For candidate MCUs/controllers, evaluate at minimum:

- independent GPIO ownership and electrical isolation from the host;
- secure storage or otherwise protected storage for trusted public keys and governance/replay state;
- sufficient non-volatile memory if persistent replay protection is required;
- hardware-supported cryptographic verification where useful;
- reliable reset and power-loss behavior;
- a practical host communication interface;
- ability to implement the frozen L4 wire protocol;
- physical packaging/wiring suitable for a bench demonstration;
- ability to keep the protected GPIO inaccessible to the host.

These are evaluation criteria derived from the L4 trust boundary; the Factory EA MVP repository does not prescribe a specific MCU family or model.

## Acceptance target

The selected MCU/controller should make it possible to implement the following physical topology:

Linux host
   |
   | untrusted transport
   v
L4 commit MCU
   |
   | sole effect path
   v
GPIO → LED / relay

and subsequently demonstrate physically:

- valid authorization → effect occurs;
- forged authorization → no effect;
- payload substitution → no effect;
- context substitution → no effect;
- stale epoch → no effect;
- revoked authority → no effect;
- replay → no effect within the stated replay boundary;
- direct host-to-actuator attempt (T8) → no physical effect;
- alternate effect interface (T10) → no physical effect.

## Scope boundary

Selecting an MCU does not by itself prove L4.

L4 remains unproven until the physical boundary is implemented and T8/T10 and the remaining acceptance criteria are demonstrated on the actual hardware.
