# termtoTable

Türkiye'deki okul takvimini (dönemler, ara tatiller, yarıyıl, resmî ve dinî
bayramlar) MEB'in resmî genelgesinden çekip yapısal bir tabloya çevirir.
Çıktı: CSV ve Excel.

## Kullanım

```bash
pip install -r requirements.txt
python termtotable/cli.py
```

## Neden basit bir scraper değil

MEB takvimi her yıl farklı bir haber ID'sinde yayımlıyor. Sabit URL'li bir
script bir yıl sonra ölmez — daha kötüsünü yapar: eski sayfayı çekmeye devam
eder ve geçen yılın tarihlerini bu yılın verisi gibi sunar.

| Katman | Dosya | İş |
|---|---|---|
| Keşif | `sources.py` | URL'yi her çalıştırmada yeniden bulur |
| Ayıklama | `parser.py` | Pozisyona değil anahtar kelimeye bağlanır |
| Doğrulama | `validate.py` | Tutarsızlık varsa süreç durur, veri yazılmaz |
| Çıktı | `build.py` | Normalize tablo + kaynak bilgisi |

Çıkış kodları: `0` başarılı · `2` kaynak bulunamadı · `3` doğrulama başarısız.

## Kaynaklar

- MEB Eğitim ve Öğretim Yılı Çalışma Takvimi genelgesi
- 2429 sayılı Ulusal Bayram ve Genel Tatiller Kanunu
- Diyanet İşleri Başkanlığı dinî günler takvimi