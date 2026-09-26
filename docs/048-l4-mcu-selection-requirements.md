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


## Execution contract and exact-byte requirements

The MCU/controller is enforcing the existing Execution Contract; it must not define a second application-level contract.

The protected execution representation remains:

```
ExecutionObject
  env_id
  context_id
  payload        exact opaque bytes
  epoch
```

The L3 authorization is bound to:

```
version
env_id
context_id
epoch
sequence
SHA-256(payload)
ea_key_id
signature
```

The controller must be able to verify the digest and signature without interpreting the domain semantics of `payload`.

The protected boundary must not:

- rewrite payload bytes;
- normalize payload encoding;
- regenerate application-level fields;
- infer authority from actuator acceptance;
- create a new authorization because a receiver accepted a command.

The effect path must receive exactly the authorized payload bytes.

## Minimum wire representation

The controller must be able to implement a deterministic encoding of the existing contract. The first prototype requires at least these message classes:

```
EXECUTION_REQUEST
  env_id
  context_id
  payload_len
  payload_bytes
  epoch

AUTHORIZATION
  version
  env_id
  context_id
  epoch
  sequence
  payload_hash
  ea_key_id
  signature
```

The transport may be UART, USB CDC, SPI, CAN, or another suitable interface. Transport selection is not itself the security boundary. All transport bytes are untrusted input.

## Commit sequencing

The controller must support the L4 positive path as an atomic enforcement sequence:

1. receive the exact execution representation and authorization;
2. verify all bindings against protected state;
3. reserve the sequence;
4. enable the sole physical effect path;
5. commit the sequence only after successful effect handoff.

A rejected authorization must never reach the protected GPIO capability. A previously accepted authorization must not become a permanent permission.

## Physical prototype topology

For the first bench demonstration, the host and protected controller should be separate physical devices.

The minimum intended topology is:

```
Linux host
   |
   | untrusted transport
   v
Trusted EA signer / protected key
   |
   | SignedAuthorization
   v
L4 commit MCU
   |
   | sole effect path
   v
GPIO -> LED / relay
```

The protected output must be wired only to the controller-owned GPIO. The host must have no alternate electrical or software-controlled path to the protected effect.

## Required physical acceptance cases

The selected MCU/controller must support a later physical demonstration of:

| Test | Required result |
| --- | --- |
| T1 valid EA authorization | effect occurs |
| T2 forged authorization | no effect |
| T3 payload substitution | no effect |
| T4 context substitution | no effect |
| T5 stale epoch | no effect |
| T6 revoked context | no effect |
| T7 replay | no effect within stated replay boundary |
| T8 direct host-to-actuator attempt | no physical effect |
| T9 attempt to overwrite epoch/revocation | blocked |
| T10 alternate effect interface | no physical effect |

T8 is the decisive hardware test: software rejection alone is insufficient. The host must be physically unable to drive the protected effect path.

## Verification and evidence boundary

The first hardware verification should combine:

- host-side adversarial test generation;
- deterministic wire vectors derived from existing conformance vectors;
- controller firmware tests;
- physical GPIO observation;
- direct-bypass testing of all available non-authorized paths.

The selected MCU/controller is suitable only if it allows these checks to be performed on the actual hardware.

The first L4 prototype claims **local non-bypassable commit mediation** under an explicit hardware trust boundary.

It does not by itself claim:

- remote attestation;
- tamper resistance against physical invasive attacks;
- production HSM certification;
- persistent replay protection across arbitrary power loss unless implemented;
- functional-safety certification;
- PLC/vendor integration;
- secure boot unless separately demonstrated;
- protection against a compromised trusted controller itself.

## What MCU selection does and does not establish

Selecting a suitable MCU/controller does not prove L4.

L4 remains unproven until the physical boundary is implemented and the acceptance criteria, including T8/T10, are demonstrated on the actual hardware.

The purpose of MCU selection is to establish a credible hardware substrate for the claim:

> The host that generates or transports an execution request does not possess the technical capability to bypass the protected commit point and cause the physical effect.
