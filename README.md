# Claude Auto Sender

Belirlediğiniz süre dolduğunda otomatik olarak **Enter** tuşuna basan bir Windows masaüstü aracı. Çalıştığı sürece bilgisayarın ekranının kararmasını veya uyku moduna geçmesini de engeller.

Özellikle uzun süre beklemeniz gereken ama ardından bir pencerede Enter'a basmanız gereken durumlar için kullanışlıdır (ör. bir sohbet/asistan uygulamasında zamanlanmış mesaj gönderimi).

## Özellikler

- Saat / dakika / saniye cinsinden geri sayım ayarlama, artı hızlı süre butonları (+30sn, +1dk, +5dk, +10dk, +30dk, +1sa)
- Başlat / Duraklat-Devam Et / Durdur / Sıfırla kontrolleri
- Görsel ilerleme çubuğu ve renkli geri sayım (son 10 saniyede sarıya döner)
- **Tekrarla modu**: süre dolduğunda Enter'ı otomatik olarak belirli sayıda (veya sınırsız) tekrar tekrar gönderir, kaç kez gönderildiğini sayar
- **Hedef pencere göstergesi**: Enter'ın gideceği, o an aktif/odaklanmış pencerenin adını canlı olarak gösterir, böylece yanlış pencereye gitmesini önler
- **Her zaman üstte tut** seçeneği ile pencereyi diğerlerinin önünde sabitleme
- Süre dolduğunda otomatik `Enter` tuşu gönderimi ve sesli bildirim
- Ayarların (süre, tekrar, üstte kalma) otomatik kaydedilip bir sonraki açılışta hatırlanması
- Klavye kısayolları: **Enter** ile başlat, **Esc** ile durdur
- Geri sayım sırasında ekranın kilitlenmesini/uyumasını engelleme
- Sade, koyu temalı arayüz (Tkinter)

## Gereksinimler

- Windows (uyku engelleme ve hedef pencere tespiti için `ctypes.windll` kullanır)
- Python 3.8+
- [pyautogui](https://pypi.org/project/PyAutoGUI/)

## Kurulum

```bash
git clone https://github.com/CaYatur/enterprogram.git
cd enterprogram
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Kullanım

```bash
python enter_presser.py
```

1. Saat, dakika ve saniye alanlarına istediğiniz süreyi girin (veya hızlı süre butonlarını kullanın).
2. İsterseniz **Tekrarla** seçeneğini işaretleyip kaç kez gönderim yapılacağını belirleyin (0 = sınırsız).
3. **▶ Başlat** butonuna basın (veya Enter tuşuna basın).
4. Geri sayım tamamlandığında uygulama otomatik olarak `Enter` tuşuna basar ve bir bildirim sesi çalar.
5. İstediğiniz an **⏸ Duraklat** ile geri sayımı geçici olarak durdurabilir, **■ Durdur** (veya Esc) ile tamamen iptal edebilirsiniz.

> Not: Uygulama, geri sayım bittiğinde etkin (aktif/odaklanmış) pencereye Enter tuşu gönderir. "Hedef pencere" alanı size o an Enter'ın hangi pencereye gideceğini canlı olarak gösterir — geri sayım bitmeden istediğiniz pencerenin orada göründüğünden emin olun.

## Lisans

Bu proje [MIT lisansı](LICENSE) ile lisanslanmıştır.
