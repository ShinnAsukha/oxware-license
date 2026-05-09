# OXware License Repository

Bu repo, OXware Hypervisor lisans kodlarını şifreli olarak saklar.

> ⚠️ **Bu repo private olmalıdır.**

## Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `.licensecodes` | Fernet ile şifrelenmiş lisans kodları (her satırda bir kod) |
| `generate_license.py` | Lisans kodu yönetim aracı |

## Lisans Kodu Formatı

```
OXWARE-XXXX-XXXX-XXXX-XXXX
```

Örnek: `OXWARE-A1B2-C3D4-E5F6-G7H8`

## Lisans Yönetimi

```bash
# Gereksinimleri kur
pip install cryptography

# Mevcut kodları listele
python generate_license.py list

# Yeni rastgele kod üret ve ekle
python generate_license.py add

# Belirli bir kod ekle
python generate_license.py add OXWARE-XXXX-XXXX-XXXX-XXXX

# Kod sil (iptal)
python generate_license.py remove OXWARE-XXXX-XXXX-XXXX-XXXX
```

Değişiklikten sonra commit ve push:
```bash
git add .licensecodes
git commit -m "Update license codes"
git push
```

## Şifreleme

Kodlar **Fernet (AES-128-CBC + HMAC-SHA256)** ile şifrelenir.
Şifreleme anahtarı OXware backend'e gömülüdür ve bu repoda bulunmaz.
