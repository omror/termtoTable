# -*- coding: utf-8 -*-
"""Resmî ve dinî tatiller.

Resmî tatiller sabit gregoryen tarihler -> hesaplanır, bakım gerektirmez.
Dinî bayramlar hicri takvimden hesaplanır (hijridate / Umm al-Qura).

Diyanet astronomik hesap kullanır, bazı yıllarda Umm al-Qura'dan 1 gün
sapabilir. Bu yüzden her satır 'dogrulama' etiketi taşır:
    diyanet    -> elle teyit edilmiş
    hesaplanan -> hicri dönüşümden üretildi, ±1 gün sapabilir
"""

from datetime import date, timedelta

# 2429 sayılı Ulusal Bayram ve Genel Tatiller Kanunu
SABIT_TATILLER = [
    ((1, 1),   "Yılbaşı"),
    ((4, 23),  "Ulusal Egemenlik ve Çocuk Bayramı"),
    ((5, 1),   "Emek ve Dayanışma Günü"),
    ((5, 19),  "Atatürk'ü Anma, Gençlik ve Spor Bayramı"),
    ((7, 15),  "Demokrasi ve Millî Birlik Günü"),
    ((8, 30),  "Zafer Bayramı"),
    ((10, 29), "Cumhuriyet Bayramı"),
]

# Diyanet takvimiyle birebir teyit ettiğin tarihler buraya.
# Yeni yıl teyit ettikçe ekle -> etiket 'hesaplanan' yerine 'diyanet' olur.
DOGRULANMIS_DINI = {
    2027: {"ramazan": date(2027, 3, 9), "kurban": date(2027, 5, 16)},
}


def _hicri_bayramlar(yil):
    """Gregoryen yıl içindeki Ramazan/Kurban bayramı 1. günlerini hesaplar."""
    try:
        from hijridate import Gregorian, Hijri
    except ImportError:
        return {}

    h_bas = Gregorian(yil, 1, 1).to_hijri().year
    h_son = Gregorian(yil, 12, 31).to_hijri().year

    cikti = {}
    for hy in range(h_bas, h_son + 1):
        # Ramazan Bayramı = 1 Şevval (10. ay), Kurban = 10 Zilhicce (12. ay)
        for ad, (ay, gun) in (("ramazan", (10, 1)), ("kurban", (12, 10))):
            try:
                g = Hijri(hy, ay, gun).to_gregorian()
            except (ValueError, OverflowError):
                continue
            d = date(g.year, g.month, g.day)
            if d.year == yil:
                cikti[ad] = d
    return cikti


def dini_bayramlar(yil):
    """[(ad, baslangic, bitis, dogrulama)] döndürür."""
    hesap = _hicri_bayramlar(yil)
    teyit = DOGRULANMIS_DINI.get(yil, {})

    cikti = []
    for anahtar, baslik, sure in (("ramazan", "Ramazan Bayramı", 3),
                                  ("kurban", "Kurban Bayramı", 4)):
        d = teyit.get(anahtar) or hesap.get(anahtar)
        if not d:
            continue
        kaynak = "diyanet" if anahtar in teyit else "hesaplanan"
        cikti.append((baslik, d, d + timedelta(days=sure - 1), kaynak))
    return cikti


def aralikta_tatiller(baslangic, bitis):
    """Verilen tarih aralığına düşen tüm resmî + dinî tatiller."""
    cikti = []
    for yil in range(baslangic.year, bitis.year + 1):
        for (ay, gun), ad in SABIT_TATILLER:
            d = date(yil, ay, gun)
            if baslangic <= d <= bitis:
                cikti.append({"ad": ad, "baslangic": d, "bitis": d,
                              "kategori": "Resmî Tatil", "dogrulama": "kanun"})

        for ad, b, e, dg in dini_bayramlar(yil):
            # Aralığa kısmen bile girse dahil et
            if b <= bitis and e >= baslangic:
                cikti.append({"ad": ad, "baslangic": b, "bitis": e,
                              "kategori": "Dinî Bayram", "dogrulama": dg})

    cikti.sort(key=lambda x: x["baslangic"])
    return cikti


if __name__ == "__main__":
    print("--- 2026-2027 öğretim yılına düşen tatiller ---")
    for t in aralikta_tatiller(date(2026, 9, 14), date(2027, 6, 25)):
        print("  %-42s %s -> %s  [%s]"
              % (t["ad"], t["baslangic"], t["bitis"], t["dogrulama"]))

    print("\n--- ileri yıllar (hepsi hesaplanan) ---")
    for yil in (2028, 2029, 2030):
        for ad, b, e, dg in dini_bayramlar(yil):
            print("  %d  %-18s %s -> %s  [%s]" % (yil, ad, b, e, dg))