"""Search result settings-consistency acceptance contract — MODEL ONLY.

This is deliberately NOT imported by the installed Command Center or invoked by
Kodi. A caller supplied JSON object is NOT trusted provenance. No production
allowance is permitted until a source-matched native request owner provides a
complete, authenticated writer timeline *including direct-file writers*.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence


def decision(before, after, *, native_witness=None, expected_request=None):
    """Return (allow:bool, reason:str) for a modeled settings-only mutation.

    before/after: immutable filesystem stamp sequences captured in the same
    original request's preflight and postflight. Non-settings guards (provider
    enabled, pinned source and dependencies, profile, cancellation, native lease,
    cache generation) MUST already pass independently; this is not their proxy.

    The proof contract defines requirements of a future native observer. It is
    NOT an authority and cannot validate native provenance or claim real direct
    writer coverage. Do not call in the shipped Search until that exists.
    """
    if before is None or after is None:
        return False, "unverifiable_settings"
    if before == after:
        return True, "unchanged_settings"
    if not isinstance(expected_request, str) or len(expected_request) != 64:
        return False, "no_bound_request"
    if not isinstance(native_witness, Mapping):
        return False, "no_native_witness"
    witness = native_witness
    if witness.get("schema") != 1:
        return False, "unknown_witness_version"
    if witness.get("request_digest") != expected_request:
        return False, "unbound_native_request"
    if witness.get("start_stamp") != before or witness.get("end_stamp") != after:
        return False, "witness_file_identity_mismatch"
    # The native owner must prove the entire request interval was observed.
    # Do NOT accept a window property, provider-returned JSON, ad hoc hash
    # equality, Python callback, filesystem timestamp or unverified event log.
    for condition in ("native_owner_verified", "complete_coverage",
                      "all_direct_file_writers_observed", "observer_continuous",
                      "native_request_completed", "source_pins_rechecked"):
        if witness.get(condition) is not True:
            return False, "unproven_" + condition
    if witness.get("event_gap") is not False or witness.get("overflow") is not False:
        return False, "missing_or_dropped_mutation"
    if witness.get("foreign_or_unattributed_write") is not False:
        return False, "unattributed_writer"
    if witness.get("shutdown_transition") is not False:
        return False, "shutdown_transition"
    first, last = witness.get("first_revision"), witness.get("last_revision")
    if (type(first) is not int or type(last) is not int or first < 0 or last <= first):
        return False, "invalid_revision_bounds"
    changes = witness.get("events")
    if (not isinstance(changes, Sequence) or isinstance(changes,(str,bytes))
            or len(changes) != last-first or len(changes) > 4096):
        return False, "incomplete_mutation_history"
    for offset, event in enumerate(changes):
        if not isinstance(event, Mapping) or event.get("revision") != first+offset+1:
            return False, "disordered_or_missing_revision"
        if event.get("source") not in ("native_kodi_settings","verified_direct_file_writer"):
            return False, "unverified_writer"
        # This must describe observed EFFECTIVE search configuration, not only
        # the difference between the initial and final XML files.
        if event.get("semantic_impact") != "bookkeeping_only":
            return False, "meaningful_or_unknown_intermediate_change"
        if event.get("verified_durable_write") is not True:
            return False, "unverified_persistence"
    return True, "proven_bookkeeping_only"


def safety_matrix():
    """Document what is and is not established by this isolated model."""
    return {
        "source_level_contract_model": True,
        "no_shipped_search_change": True,
        "real_native_evidence_producer": False,
        "all_direct_file_writers_observed_on_android": False,
        "kodi_runtime_verified": False,
        "no_apk_or_signing": True,
    }
