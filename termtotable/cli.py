# -*- coding: utf-8 -*-
"""termtoTable komut satırı arayüzü.

    python cli.py                      -> içinde bulunulan öğretim yılı
    python cli.py --year 2027-2028
    python cli.py --url <meb_url>      -> keşfi atla, adresi sen ver
"""

import argparse
import sys
from datetime import date

from build import csv_yaz, tablo_kur, xlsx_yaz
from parser import ayikla, ogretim_yili_bul
from sources import KaynakBulunamadi, kaynak_bul
from validate import DogrulamaHatasi, dogrula


def gecerli_ogretim_yili(bugun=None):
    """Eylül-Ağustos döngüsüne göre içinde bulunulan öğretim yılı."""
    b = bugun or date.today()
    if b.month >= 9:
        return "%d-%d" % (b.year, b.year + 1)
    return "%d-%d" % (b.year - 1, b.year)


def main():
    p = argparse.ArgumentParser(description="Türkiye okul takvimi -> tablo")
    p.add_argument("--year", help="öğretim yılı, örn. 2027-2028")
    p.add_argument("--url", help="MEB haber adresini elle ver (keşfi atlar)")
    p.add_argument("--out", default="out", help="çıktı klasörü (varsayılan: out)")
    a = p.parse_args()

    yil = a.year or gecerli_ogretim_yili()
    print("termtoTable — %s öğretim yılı" % yil)

    # 1) Kaynağı bul
    try:
        url, metin = kaynak_bul(yil, manuel_url=a.url)
    except KaynakBulunamadi as e:
        print("\n[HATA] %s" % e, file=sys.stderr)
        return 2
    print("[ok] Kaynak: %s" % url)

    # 2) Sayfa gerçekten istediğimiz yıla mı ait?
    metindeki = ogretim_yili_bul(metin)
    if metindeki and metindeki != yil:
        print("[HATA] Sayfa %s yılına ait, %s isteniyordu." % (metindeki, yil),
              file=sys.stderr)
        return 2

    # 3) Ayıkla
    olaylar, uyarilar = ayikla(metin)
    for u in uyarilar:
        print("  [uyarı] %s" % u, file=sys.stderr)

    # 4) Doğrula — hata varsa dosya YAZILMAZ
    try:
        _, dog_uyari = dogrula(olaylar, yil)
    except DogrulamaHatasi as e:
        print("\n[HATA] %s" % e, file=sys.stderr)
        return 3
    for u in dog_uyari:
        print("  [uyarı] %s" % u, file=sys.stderr)

    # 5) Tabloyu kur ve yaz
    satirlar = tablo_kur(olaylar, yil, url)
    csv_yolu = "%s/termtotable_%s.csv" % (a.out, yil)
    xlsx_yolu = "%s/termtotable_%s.xlsx" % (a.out, yil)
    csv_yaz(satirlar, csv_yolu)
    xlsx_yaz(satirlar, xlsx_yolu, url)

    print("\n[ok] %d kayıt yazıldı:" % len(satirlar))
    print("  %s" % csv_yolu)
    print("  %s" % xlsx_yolu)
    for s in satirlar:
        print("  %2d %-16s %-42s %s -> %-10s [%s]"
              % (s["id"], s["kategori"], s["olay"], s["baslangic"],
                 s["bitis"] or "-", s["dogrulama"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())