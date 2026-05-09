#!/usr/bin/env python3
"""
OXware Lisans Kodu Üretici
──────────────────────────
Yeni lisans kodları eklemek veya mevcut listeyi güncellemek için kullanın.

Kullanım:
  python generate_license.py list          # Mevcut kodları listele
  python generate_license.py add           # Yeni rastgele kod ekle
  python generate_license.py add OXWARE-XXXX-XXXX-XXXX-XXXX  # Belirli kod ekle
  python generate_license.py remove OXWARE-XXXX-XXXX-XXXX-XXXX  # Kod sil
"""

import sys
import os
import base64
import hashlib
import random
import string

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("cryptography kütüphanesi gerekli: pip install cryptography")
    sys.exit(1)

CODES_FILE = ".licensecodes"
PASSPHRASE = b'OXware-License-Secret-2024-ShinnAsukha'


def get_fernet():
    key_bytes = hashlib.sha256(PASSPHRASE).digest()
    key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(key)


def load_codes():
    if not os.path.exists(CODES_FILE):
        return []
    f = get_fernet()
    with open(CODES_FILE, 'rb') as fp:
        data = fp.read().strip()
    decrypted = f.decrypt(data)
    return [c.strip() for c in decrypted.decode('utf-8').splitlines() if c.strip()]


def save_codes(codes):
    f = get_fernet()
    content = '\n'.join(codes) + '\n'
    encrypted = f.encrypt(content.encode('utf-8'))
    with open(CODES_FILE, 'wb') as fp:
        fp.write(encrypted)
    print(f"✓ {CODES_FILE} güncellendi ({len(codes)} kod)")


def generate_code():
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(random.choices(chars, k=4)) for _ in range(4)]
    return 'OXWARE-' + '-'.join(parts)


def validate_format(code):
    parts = code.split('-')
    return len(parts) == 5 and parts[0] == 'OXWARE' and all(len(p) == 4 for p in parts[1:])


def cmd_list():
    codes = load_codes()
    if not codes:
        print("Henüz lisans kodu yok.")
        return
    print(f"\n{'─'*40}")
    print(f"  Toplam {len(codes)} lisans kodu:")
    print(f"{'─'*40}")
    for i, c in enumerate(codes, 1):
        print(f"  {i:3}. {c}")
    print(f"{'─'*40}\n")


def cmd_add(code=None):
    codes = load_codes()
    if code is None:
        code = generate_code()
        print(f"Üretilen kod: {code}")
    else:
        code = code.upper().strip()
        if not validate_format(code):
            print(f"✗ Geçersiz format: {code}")
            print("  Format: OXWARE-XXXX-XXXX-XXXX-XXXX (büyük harf + rakam)")
            return
    if code in codes:
        print(f"✗ Bu kod zaten mevcut: {code}")
        return
    codes.append(code)
    save_codes(codes)
    print(f"✓ Eklendi: {code}")


def cmd_remove(code):
    code = code.upper().strip()
    codes = load_codes()
    if code not in codes:
        print(f"✗ Kod bulunamadı: {code}")
        return
    codes.remove(code)
    save_codes(codes)
    print(f"✓ Silindi: {code}")


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == 'list':
        cmd_list()
    elif args[0] == 'add':
        cmd_add(args[1] if len(args) > 1 else None)
    elif args[0] == 'remove' and len(args) > 1:
        cmd_remove(args[1])
    else:
        print(__doc__)
