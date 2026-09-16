# -*- coding: utf-8 -*-
"""Ayıklanan takvimin akıl sağlığı kontrolü. 
Scraper her zaman kırılabilir; önemli olan kırıldığını FARK ETMEK.
Bir kural tutmazsa hata fırlatılır ve veri kaydedilmez.
"""

ZORUNLU = ["birinci_donem", "ara_tatil_1", "yariyil_tatili",
           "ikinci_donem", "ara_tatil_2"]

PAZARTESI, CUMA = 0, 4
GUN_ADI = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]


class DogrulamaHatasi(Exception):
    pass


def dogrula(olaylar, ogretim_yili):
    """(hatalar, uyarilar) döndürür. Hata varsa exception fırlatır.

    hata  = veri kesin yanlış, kaydetme
    uyari = tuhaf ama mümkün, kaydet ama haber ver
    """
    hatalar = []
    uyarilar = []

    # 1) Zorunlu olayların hepsi var mı?
    for kod in ZORUNLU:
        if kod not in olaylar:
            hatalar.append("Zorunlu olay eksik: %s" % kod)
    if hatalar:
        raise DogrulamaHatasi("\n  - ".join(["Doğrulama başarısız:"] + hatalar))

    bd_b, bd_e = olaylar["birinci_donem"]
    id_b, id_e = olaylar["ikinci_donem"]
    at1_b, at1_e = olaylar["ara_tatil_1"]
    at2_b, at2_e = olaylar["ara_tatil_2"]
    yt_b, yt_e = olaylar["yariyil_tatili"]

    # 2) Öğretim yılı etiketiyle tarihler tutuyor mu?
    bas_yil, bit_yil = [int(x) for x in ogretim_yili.split("-")]
    if bd_b.year != bas_yil:
        hatalar.append("1. dönem %d'de başlamalı, %s bulundu" % (bas_yil, bd_b))
    if id_e and id_e.year != bit_yil:
        hatalar.append("2. dönem %d'de bitmeli, %s bulundu" % (bit_yil, id_e))

    # 3) Kronolojik sıra
    sirali = [("1. dönem başl.", bd_b), ("1. ara tatil", at1_b),
              ("1. dönem bitiş", bd_e), ("yarıyıl tatili", yt_b),
              ("2. dönem başl.", id_b), ("2. ara tatil", at2_b)]
    for (ad1, d1), (ad2, d2) in zip(sirali, sirali[1:]):
        if d1 >= d2:
            hatalar.append("Sıra bozuk: %s (%s) >= %s (%s)" % (ad1, d1, ad2, d2))

    # 4) 1. dönem eylülde ve pazartesi başlamalı
    if bd_b.month != 9:
        hatalar.append("1. dönem eylülde başlamalı, %s bulundu" % bd_b)
    if bd_b.weekday() != PAZARTESI:
        uyarilar.append("1. dönem pazartesi başlamıyor (%s)" % GUN_ADI[bd_b.weekday()])

    # 5) Dönem uzunluğu makul mü?
    for ad, b, e in (("1. dönem", bd_b, bd_e), ("2. dönem", id_b, id_e)):
        if e is None:
            continue
        gun = (e - b).days + 1
        if not 100 <= gun <= 160:
            hatalar.append("%s uzunluğu şüpheli: %d takvim günü" % (ad, gun))

    # 6) Ara tatiller Pazartesi-Cuma, 5 gün
    for ad, b, e in (("1. ara tatil", at1_b, at1_e), ("2. ara tatil", at2_b, at2_e)):
        gun = (e - b).days + 1
        if gun != 5:
            uyarilar.append("%s 5 gün değil: %d gün" % (ad, gun))
        if b.weekday() != PAZARTESI or e.weekday() != CUMA:
            uyarilar.append("%s Pzt-Cum değil: %s-%s"
                            % (ad, GUN_ADI[b.weekday()], GUN_ADI[e.weekday()]))

    # 7) Yarıyıl tatili ~2 hafta
    yt_gun = (yt_e - yt_b).days + 1
    if not 10 <= yt_gun <= 18:
        uyarilar.append("Yarıyıl tatili alışılmadık uzunlukta: %d gün" % yt_gun)

    # 8) Ara tatiller kendi döneminin içinde mi?
    if not (bd_b < at1_b and at1_e < bd_e):
        hatalar.append("1. ara tatil 1. dönemin içinde değil")
    if id_e and not (id_b < at2_b and at2_e < id_e):
        hatalar.append("2. ara tatil 2. dönemin içinde değil")

    # 9) Yarıyıl tatili iki dönemin arasında mı?
    if not (bd_e < yt_b and yt_e < id_b):
        hatalar.append("Yarıyıl tatili iki dönemin arasında değil")

    if hatalar:
        raise DogrulamaHatasi(
            "Doğrulama başarısız (%d hata):\n  - %s\n\n"
            "MEB metninin biçimi değişmiş olabilir. Veri KAYDEDİLMEDİ."
            % (len(hatalar), "\n  - ".join(hatalar)))

    return hatalar, uyarilar


if __name__ == "__main__":
    from datetime import date

    gecerli = {
        "birinci_donem":  (date(2026, 9, 14), date(2027, 1, 22)),
        "ara_tatil_1":    (date(2026, 11, 16), date(2026, 11, 20)),
        "yariyil_tatili": (date(2027, 1, 25), date(2027, 2, 5)),
        "ikinci_donem":   (date(2027, 2, 8), date(2027, 6, 25)),
        "ara_tatil_2":    (date(2027, 3, 8), date(2027, 3, 12)),
    }

    print("--- geçerli veri ---")
    h, u = dogrula(gecerli, "2026-2027")
    print("hata:", h or "yok", "| uyarı:", u or "yok")

    print("\n--- bozuk veri: ara tatil dönem dışında ---")
    bozuk = dict(gecerli)
    bozuk["ara_tatil_1"] = (date(2027, 3, 1), date(2027, 3, 5))
    try:
        dogrula(bozuk, "2026-2027")
        print("SORUN: bozuk veri geçti!")
    except DogrulamaHatasi as e:
        print(e)