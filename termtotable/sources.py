# -*- coding: utf-8 -*-
"""MEB çalışma takvimi haberini bulma ve çekme.

MEB takvimi her yıl farklı haber ID'sinde yayımlıyor. URL'yi her
çalıştırmada yeniden buluyoruz:
    1. cache -> daha önce bulunmuş ID
    2. slug  -> URL'yi başlık kalıbından kurma
    3. manuel -> kullanıcının --url ile verdiği adres

Hiçbiri tutmazsa hata verir. Sessizce eski veriye DÜŞMEZ; bu projede
en tehlikeli hata yanlış veri değil, fark edilmeyen eski veridir.
"""

import html as htmlmod
import json
import re
from pathlib import Path

import requests

from parser import katla

BASE = "https://www.meb.gov.tr"
KNOWN_IDS = Path(__file__).resolve().parent.parent / "data" / "known_ids.json"

# Doğrulanmış çapa: bu haber gerçekten var
ANCHOR = {"2026-2027": 41057}

HEADERS = {
    # MEB boş User-Agent'a 403 dönüyor, gerçekçi bir tarayıcı kimliği şart
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept-Language": "tr-TR,tr;q=0.9",
}


class KaynakBulunamadi(RuntimeError):
    pass


def duz_metin(html):
    """HTML'den script/style atıp düz metne indirger."""
    html = re.sub(r"(?is)<(script|style|nav|footer).*?</\1>", " ", html)
    metin = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", htmlmod.unescape(metin)).strip()


def cek(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200 and len(r.text) > 500:
            return r.text
    except requests.RequestException:
        pass
    return None


def takvim_haberi_mi(metin, beklenen_yil):
    """Sayfa gerçekten istenen yılın takvim haberi mi?"""
    k = katla(metin)
    bas, bit = beklenen_yil.split("-")
    if "%s-%s" % (bas, bit) not in k:
        return False
    return "ara tatil" in k and "donem" in k


def known_ids():
    if KNOWN_IDS.exists():
        return json.loads(KNOWN_IDS.read_text(encoding="utf-8"))
    return dict(ANCHOR)


def known_ids_yaz(d):
    KNOWN_IDS.parent.mkdir(parents=True, exist_ok=True)
    KNOWN_IDS.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def slug(yil):
    return "%s-egitim-ogretim-yili-takvimi-aciklandi" % yil


def kaynak_bul(ogretim_yili, manuel_url=None):
    """(url, metin) döndürür."""
    if manuel_url:
        html = cek(manuel_url)
        if not html:
            raise KaynakBulunamadi("Verilen URL çekilemedi: %s" % manuel_url)
        metin = duz_metin(html)
        if not takvim_haberi_mi(metin, ogretim_yili):
            raise KaynakBulunamadi(
                "Verilen sayfa %s takvim haberine benzemiyor." % ogretim_yili)
        return manuel_url, metin

    # 1) Cache'lenmiş ID
    hid = known_ids().get(ogretim_yili)
    if hid:
        url = "%s/%s/haber/%d/tr" % (BASE, slug(ogretim_yili), hid)
        html = cek(url)
        if html:
            metin = duz_metin(html)
            if takvim_haberi_mi(metin, ogretim_yili):
                return url, metin

    # 2) Slug ile dene (CMS slug'dan route ediyorsa ID gerekmez)
    for aday in ("%s/%s" % (BASE, slug(ogretim_yili)),):
        html = cek(aday)
        if html:
            metin = duz_metin(html)
            if takvim_haberi_mi(metin, ogretim_yili):
                return aday, metin

    raise KaynakBulunamadi(
        "%s çalışma takvimi haberi bulunamadı.\n"
        "  - Takvim henüz yayımlanmamış olabilir (MEB genelde haziranda açıklıyor)\n"
        "  - MEB isteği engellemiş olabilir (403)\n"
        "  Haberi elle bulup şöyle verebilirsin:\n"
        "    python cli.py --year %s --url <meb_haber_url>"
        % (ogretim_yili, ogretim_yili))


if __name__ == "__main__":
    url, metin = kaynak_bul("2026-2027")
    print("URL:", url)
    print("Metin uzunluğu:", len(metin))
    print("İlk 300 karakter:\n", metin[:300])