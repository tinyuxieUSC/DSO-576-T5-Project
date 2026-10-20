"""One canonical cleaning pipeline shared by the CSV and JSON adapters."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import hmac
import math
import re

NOT_REPORTED = 'NOT_REPORTED'
UUID = re.compile(r'^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')
COUNT_COLUMNS = ['listens', 'valid_mbid_listens', 'missing_mbid_listens', 'invalid_mbid_listens']
GROUP_COLUMNS = ['play_date', 'client', 'client_version', 'account_key', 'client_type']

class RejectedEvent(ValueError):
    pass


def json_fields(event):
    if not isinstance(event, dict):
        raise RejectedEvent('non_object_event')
    tm = event.get('track_metadata', {})
    if not isinstance(tm, dict):
        raise RejectedEvent('non_object_track_metadata')
    ai = tm.get('additional_info', {})
    if not isinstance(ai, dict):
        raise RejectedEvent('non_object_additional_info')
    return (event.get('user_id'), event.get('timestamp'), ai.get('submission_client'),
            ai.get('submission_client_version'), ai.get('recording_mbid'))


def csv_fields(event):
    return tuple(event.get(k) for k in ('user_id', 'timestamp', 'ai_submission_client',
                                      'ai_submission_client_version', 'ai_recording_mbid'))


def clean_event(fields, secret: bytes, aliases: dict, classification: dict):
    account, timestamp, client, version, mbid = fields
    if timestamp is None or timestamp == '':
        raise RejectedEvent('absent_timestamp')
    try:
        if isinstance(timestamp, bool):
            raise ValueError
        seconds = float(timestamp)
    except (TypeError, ValueError):
        raise RejectedEvent('nonnumeric_timestamp') from None
    try:
        if not math.isfinite(seconds):
            raise ValueError
        played = datetime.fromtimestamp(seconds, timezone.utc)
    except (OverflowError, ValueError, OSError):
        raise RejectedEvent('unrepresentable_timestamp') from None
    valid_account = type(account) is int and account > 0
    if isinstance(account, str) and re.fullmatch(r'\+?[0-9]+', account.strip()):
        account = int(account.strip())
        valid_account = account > 0
    key = hmac.new(secret, str(account).encode(), hashlib.sha256).hexdigest() if valid_account else None
    raw_label = client.strip() if isinstance(client, str) and client.strip() else NOT_REPORTED
    name = aliases.get(raw_label.casefold(), raw_label.casefold()) if raw_label != NOT_REPORTED else NOT_REPORTED
    version = version.strip() if isinstance(version, str) and version.strip() else NOT_REPORTED
    kind = ('importer' if name in classification['importers'] else
            'regular' if name in classification['regular_clients'] else 'unknown')
    if mbid is None or (isinstance(mbid, str) and not mbid.strip()):
        status = 'missing'
    elif isinstance(mbid, str) and UUID.fullmatch(mbid.strip()):
        status = 'valid'
    else:
        status = 'invalid'
    return {'play_date': played.date(), 'client': name, 'client_version': version,
            'account_key': key, 'client_type': kind, 'listens': 1,
            'valid_mbid_listens': int(status == 'valid'),
            'missing_mbid_listens': int(status == 'missing'),
            'invalid_mbid_listens': int(status == 'invalid')}, raw_label, played
