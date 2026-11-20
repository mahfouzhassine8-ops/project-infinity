"""Print only the fixed 2103518 decision codes from a private Kodi/logcat stream."""
import json
import sys


OUTCOMES = {
    'selection': {
        'saved_item_missing_or_ineligible', 'saved_item_changed', 'unverified_identity',
    },
    'source_memory': {
        'preferred_route_failure_threshold', 'typed_helper_resolver_available',
    },
    'original_provider': {
        'contract_catalog_digest_mismatch', 'provider_absent_from_contract_catalog',
        'provider_manifest_id_mismatch', 'provider_version_not_approved',
        'provider_source_pin_mismatch', 'provider_source_changed_during_check',
        'provider_or_contract_unreadable', 'provider_disabled', 'no_verified_contract',
    },
    'original_route': {
        'invalid_uri', 'provider_or_uri_path_mismatch', 'duplicate_route_arguments',
        'provider_action_or_media_type_mismatch', 'provider_action_mismatch',
        'typed_identity_mismatch', 'episode_arguments_on_movie', 'episode_scope_unsupported',
        'episode_coordinates_mismatch', 'route_parse_failed', 'missing_saved_identity',
    },
    'remembered_provider': {
        'contract_missing', 'contract_pins_invalid', 'provider_id_invalid',
        'route_invalid', 'provider_unavailable', 'source_pin_mismatch_or_unreadable',
        'provider_disabled',
    },
    'target': {
        'unverified_identity', 'remembered_route_accepted', 'original_route_accepted',
    },
    'recovery_required': {
        'remembered_route_previously_failed', 'remembered_route_fingerprint_mismatch',
        'remembered_provider_or_route_rejected', 'original_route_previously_failed',
        'original_route_unavailable',
    },
    'checkpoint_choice': {'resume', 'begin', 'cancelled'},
    'original_handoff': {'dispatch_failed', 'dispatch_returned'},
    'recovery': {
        'unverified_identity', 'native_failure_ticket_received',
        'native_ticket_original_fingerprint_mismatch',
        'native_ticket_destination_fingerprint_mismatch',
        'native_failure_ticket_verified', 'revalidation_selected_direct_route',
        'unavailable_without_native_attempt', 'alternatives_available',
        'no_compatible_alternative', 'alternative_verified', 'cancelled_or_changed', 'failed',
    },
    'recovery_handoff': {'playback_verified', 'dispatch_failed', 'dispatch_returned'},
}


def decision(line):
    _, matched, raw = line.partition('INFINITY_SAVED_NAVIGATION ')
    if not matched or len(raw) > 1024:
        return None
    try:
        row = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(row, dict) or set(row) != {
        'schema', 'stage', 'epoch_ms', 'monotonic_ms', 'boundary', 'outcome',
    }:
        return None
    if type(row['schema']) is not int or row['schema'] != 1 or row['stage'] != 'continue_navigation':
        return None
    boundary, outcome = row['boundary'], row['outcome']
    if (not isinstance(boundary, str) or not isinstance(outcome, str)
            or outcome not in OUTCOMES.get(boundary, ())):
        return None
    epoch_ms, monotonic_ms = row['epoch_ms'], row['monotonic_ms']
    if (type(epoch_ms) is not int or not 0 <= epoch_ms < 2**53
            or type(monotonic_ms) not in (int, float) or not 0 <= monotonic_ms < 2**53):
        return None
    return row


if __name__ == '__main__':
    for line in sys.stdin:
        row = decision(line)
        if row is not None:
            print(json.dumps(row, sort_keys=True), flush=True)
