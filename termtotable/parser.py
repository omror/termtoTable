# -*- coding: utf-8 -*-
import re
from datetime import date

AYLAR = {
    "ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6,
    "temmuz": 7, "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12,
}

TEK_TARIH = re.compile(r"(\d{1,2})\s+([a-z]+)\s+(20\d{2})")
# "7-11 Eylül 2026" -> tek seferde iki tarih
ARALIK_TARIH = re.compile(r"(\d{1,2})\s*[-–/]\s*(\d{1,2})\s+([a-z]+)\s+(20\d{2})")

KATLAMA = str.maketrans("İıĞğŞşÇçÖöÜü", "IiGgSsCcOoUu")

# olay kodu -> (aranacak ifade, kaç tarih, yön)
#   ileri = tarihler ifadeden SONRA | geri = ÖNCE | cift = önce ileri, olmazsa geri
OLAYLAR = {
    "mesleki_calisma": (r"mesleki calisma",                            1, "ileri"),
    "uyum_egitimi":    (r"uyum egitim",                                2, "cift"),
    "birinci_donem":   (r"birinci donem[,\s]",                         2, "ileri"),
    "ara_tatil_1":     (r"birinci donem ara tatili",                   2, "ileri"),
    "yariyil_tatili":  (r"yariyil tatili",                             2, "ileri"),
    "ikinci_donem":    (r"ikinci donem ise",                           1, "ileri"),
    "ara_tatil_2":     (r"ikinci donemin ara tatili",                  2, "ileri"),
    "yil_sonu":        (r"egitim ve ogretim yili,\s*\d{1,2}\s+\w+\s+20\d{2}", 1, "ileri"),
}


def katla(metin):
    """Türkçe karakterleri ASCII'ye çevirip küçültür. Uzunluk korunur."""
    return metin.translate(KATLAMA).lower()


def tarihe_cevir(gun, ay, yil):
    ay_no = AYLAR.get(ay)
    if not ay_no:
        return None
    try:
        return date(int(yil), ay_no, int(gun))
    except ValueError:
        return None


def tarih_gruplari(parca):
    """Parçadaki tarihleri SIRAYLA gruplar halinde döndürür.

    Aralık ("7-11 Eylül 2026") = tek grup, iki tarih.
    Tekil tarih ("14 Eylül 2026") = tek grup, bir tarih.
    Aralığın içindeki tekil eşleşmeler ayrıca sayılmaz.
    """
    gruplar = []
    kapali = []   # aralıkların kapladığı karakter bölgeleri

    for m in ARALIK_TARIH.finditer(parca):
        b = tarihe_cevir(m.group(1), m.group(3), m.group(4))
        e = tarihe_cevir(m.group(2), m.group(3), m.group(4))
        if b and e:
            gruplar.append((m.start(), [b, e]))
            kapali.append((m.start(), m.end()))

    for m in TEK_TARIH.finditer(parca):
        if any(a <= m.start() < b for a, b in kapali):
            continue
        d = tarihe_cevir(m.group(1), m.group(2), m.group(3))
        if d:
            gruplar.append((m.start(), [d]))

    gruplar.sort(key=lambda g: g[0])
    return [g[1] for g in gruplar]


def tarihleri_bul(metin):
    """Metindeki tüm tarihleri düz liste olarak döndürür."""
    duz = []
    for grup in tarih_gruplari(katla(metin)):
        duz.extend(grup)
    return duz


def pencereden_oku(parca, adet, sondan=False):
    """Parçadan 'adet' tarih toplar. sondan=True ise sondaki gruplardan."""
    gruplar = tarih_gruplari(parca)
    if not gruplar:
        return None

    toplanan = []
    for grup in (reversed(gruplar) if sondan else gruplar):
        toplanan = (grup + toplanan) if sondan else (toplanan + grup)
        if len(toplanan) >= adet:
            return toplanan[-adet:] if sondan else toplanan[:adet]
    return None


def tarihleri_ara(katlanmis, konum, adet, yon="ileri", pencere=260):
    if yon in ("ileri", "cift"):
        sonuc = pencereden_oku(katlanmis[konum:konum + pencere], adet)
        if sonuc:
            return sonuc
    if yon in ("geri", "cift"):
        bas = max(0, konum - pencere)
        return pencereden_oku(katlanmis[bas:konum], adet, sondan=True)
    return None


def ayikla(metin):
    """Metinden olayları çıkarır -> ({kod: (baslangic, bitis)}, [uyarilar])"""
    k = katla(metin)
    sonuc = {}
    uyarilar = []

    for kod, (ifade, adet, yon) in OLAYLAR.items():
        m = re.search(ifade, k)
        if not m:
            uyarilar.append("'%s': ifade metinde yok" % kod)
            continue
        tarihler = tarihleri_ara(k, m.start(), adet, yon)
        if not tarihler:
            uyarilar.append("'%s': ifade bulundu ama %d tarih okunamadı" % (kod, adet))
            continue
        sonuc[kod] = (tarihler[0], tarihler[1] if adet == 2 else None)

    # 2. dönemin bitişi ayrı cümlede yazılıyor; yıl sonu tarihiyle aynı
    if "ikinci_donem" in sonuc and "yil_sonu" in sonuc:
        sonuc["ikinci_donem"] = (sonuc["ikinci_donem"][0], sonuc["yil_sonu"][0])

    return sonuc, uyarilar


def ogretim_yili_bul(metin):
    m = re.search(r"(20\d{2})\s*[-–]\s*(20\d{2})\s+egitim", katla(metin))
    return "%s-%s" % (m.group(1), m.group(2)) if m else None