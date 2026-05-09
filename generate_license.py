#!/usr/bin/env python3
"""
OXware Lisans Kodu Üretici & Takip Aracı
─────────────────────────────────────────
Kullanım:
  python generate_license.py list                              # Mevcut kodları listele
  python generate_license.py add                               # Yeni rastgele kod ekle
  python generate_license.py add OXWARE-XXXX-XXXX-XXXX-XXXX  # Belirli kod ekle
  python generate_license.py remove OXWARE-XXXX-XXXX-XXXX-XXXX  # Kod sil (iptal)

  # Sunucudaki aktivasyonları göster (kim hangi IP'den aktifleştirmiş)
  python generate_license.py activations --server https://IP:8006 --user admin --pass ŞIFRE
"""

import sys
import os
import base64
import hashlib
import random
import string
import json
import getpass

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
    W = 44
    print(f"\n{'─'*W}")
    print(f"  Toplam {len(codes)} lisans kodu")
    print(f"{'─'*W}")
    for i, c in enumerate(codes, 1):
        print(f"  {i:3}. {c}")
    print(f"{'─'*W}\n")


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
    print(f"✓ Silindi (iptal edildi): {code}")


def cmd_activations(server, username, password):
    """Sunucudaki aktivasyon kayıtlarını çek ve göster."""
    try:
        import urllib.request
        import urllib.error

        # 1. Token al
        login_url = f"{server.rstrip('/')}/api/auth/login"
        login_data = json.dumps({"username": username, "password": password}).encode()
        req = urllib.request.Request(
            login_url,
            data=login_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        # Self-signed SSL sertifikası için
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            login_resp = json.loads(resp.read())

        token = login_resp.get("token") or login_resp.get("access_token")
        if not token:
            print(f"✗ Giriş başarısız: {login_resp.get('error', 'Bilinmeyen hata')}")
            return

        # 2. Aktivasyonları çek
        act_url = f"{server.rstrip('/')}/api/license/activations"
        req2 = urllib.request.Request(
            act_url,
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req2, context=ctx, timeout=10) as resp2:
            data = json.loads(resp2.read())

        activations = data.get("activations", [])

        if not activations:
            print("\n  Henüz hiç aktivasyon kaydı yok.\n")
            return

        # Lokal kod listesiyle karşılaştır
        local_codes = load_codes()
        local_hashes = {hashlib.sha256(c.encode()).hexdigest(): c for c in local_codes}

        W = 80
        print(f"\n{'─'*W}")
        print(f"  {'KOD ÖNEKİ':<18}  {'IP ADRESİ':<18}  {'İLK AKTİVASYON':<20}  {'SON':<20}  {'SAYIM'}")
        print(f"{'─'*W}")

        for act in activations:
            prefix     = act.get("code_prefix", "?")
            ip         = act.get("ip", "?")
            first      = act.get("first_activated", "?")[:16]
            last       = act.get("last_activated", "?")[:16]
            count      = act.get("activation_count", 1)
            code_hash  = act.get("code_hash", "")

            # Kod hâlâ geçerli mi?
            still_valid = "✓" if code_hash in local_hashes else "✗ İPTAL"

            print(f"  {prefix:<18}  {ip:<18}  {first:<20}  {last:<20}  {count}x  {still_valid}")

        print(f"{'─'*W}")
        print(f"  Toplam {len(activations)} aktivasyon kaydı\n")

    except urllib.error.URLError as e:
        print(f"✗ Sunucuya bağlanılamadı: {e.reason}")
    except Exception as e:
        print(f"✗ Hata: {e}")


def parse_activations_args(args):
    """--server, --user, --pass argümanlarını parse et."""
    params = {"server": None, "user": None, "password": None}
    i = 0
    while i < len(args):
        if args[i] == "--server" and i + 1 < len(args):
            params["server"] = args[i + 1]; i += 2
        elif args[i] == "--user" and i + 1 < len(args):
            params["user"] = args[i + 1]; i += 2
        elif args[i] in ("--pass", "--password") and i + 1 < len(args):
            params["password"] = args[i + 1]; i += 2
        else:
            i += 1
    return params


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args or args[0] == 'list':
        cmd_list()

    elif args[0] == 'add':
        cmd_add(args[1] if len(args) > 1 else None)

    elif args[0] == 'remove' and len(args) > 1:
        cmd_remove(args[1])

    elif args[0] == 'activations':
        p = parse_activations_args(args[1:])
        if not p["server"]:
            p["server"] = input("Sunucu URL (örn. https://94.177.147.198:8006): ").strip()
        if not p["user"]:
            p["user"] = input("Kullanıcı adı: ").strip()
        if not p["password"]:
            p["password"] = getpass.getpass("Şifre: ")
        cmd_activations(p["server"], p["user"], p["password"])

    else:
        print(__doc__)
