#!/usr/bin/env python3
"""Normalize phone numbers in the `leads` table to E.164.

Creates a backup `crm_database.db.bak` before modifying data.
"""
import os
import shutil
import sqlite3
import phonenumbers
from phonenumbers import NumberParseException
import argparse
import re

DB = 'crm_database.db'
BACKUP = DB + '.bak'


def format_phone_e164(phone):
    phone = (phone or '').strip()
    if not phone:
        return ''
    try:
        if phone.startswith('+'):
            pn = phonenumbers.parse(phone, None)
        else:
            pn = phonenumbers.parse(phone, 'IN')
        if phonenumbers.is_valid_number(pn):
            return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
        else:
            return None
    except NumberParseException:
        return None


def main():
    parser = argparse.ArgumentParser(description='Normalize phone numbers to E.164')
    parser.add_argument('--auto-fix', action='store_true', help='Attempt conservative auto-fixes for invalid numbers')
    args = parser.parse_args()

    auto_fix = args.auto_fix

    if not os.path.exists(DB):
        print(f"Database file '{DB}' not found. Run the app first to create it.")
        return 2

    if not os.path.exists(BACKUP):
        shutil.copy2(DB, BACKUP)
        print(f"Backup created: {BACKUP}")
    else:
        print(f"Backup already exists: {BACKUP}")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("SELECT id, phone FROM leads")
    rows = cursor.fetchall()

    updated = []
    invalid = []

    for row in rows:
        lead_id, phone = row
        if not phone:
            continue
        formatted = format_phone_e164(phone)
        if formatted is None:
            # try conservative auto-fix heuristics when requested
            fixed = None
            if auto_fix:
                digits = re.sub(r'\D', '', phone)
                candidate = None
                # common patterns
                if len(digits) == 10:
                    # try as India then US
                    try_candidate = '+' + '91' + digits
                    if format_phone_e164(try_candidate) is not None:
                        candidate = try_candidate
                    else:
                        try_candidate = '+' + '1' + digits
                        if format_phone_e164(try_candidate) is not None:
                            candidate = try_candidate
                elif len(digits) == 11 and digits.startswith('1'):
                    candidate = '+' + digits
                elif len(digits) >= 11 and digits.startswith('91'):
                    candidate = '+' + digits

                # final attempt: if original started with + and had digits, try parsing with no spaces
                if candidate is None and phone.strip().startswith('+'):
                    compact = '+' + re.sub(r'\D', '', phone)
                    if format_phone_e164(compact) is not None:
                        candidate = compact

                if candidate:
                    fixed = format_phone_e164(candidate)

            if fixed is None:
                invalid.append((lead_id, phone))
                continue
            else:
                cursor.execute("UPDATE leads SET phone = ? WHERE id = ?", (fixed, lead_id))
                updated.append((lead_id, phone, fixed))
        else:
            if formatted != phone:
                cursor.execute("UPDATE leads SET phone = ? WHERE id = ?", (formatted, lead_id))
                updated.append((lead_id, phone, formatted))

    conn.commit()
    conn.close()

    print(f"Processed {len(rows)} leads. Updated: {len(updated)}. Invalid: {len(invalid)}")
    if updated:
        print('\nSample updates:')
        for u in updated[:10]:
            print(f" - id={u[0]}: {u[1]} -> {u[2]}")
    if invalid:
        print('\nInvalid phone entries (not updated):')
        for iv in invalid[:20]:
            print(f" - id={iv[0]}: {iv[1]}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
