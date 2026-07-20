# Claude Auto Sender

Belirlediğiniz süre dolduğunda otomatik olarak **Enter** tuşuna basan, basit bir Windows masaüstü aracı. Çalıştığı sürece bilgisayarın ekranının kararmasını veya uyku moduna geçmesini de engeller.

Özellikle uzun süre beklemeniz gereken ama ardından bir pencerede Enter'a basmanız gereken durumlar için kullanışlıdır (ör. bir sohbet/asistan uygulamasında zamanlanmış mesaj gönderimi).

## Özellikler

- Saat / dakika / saniye cinsinden geri sayım ayarlama
- Başlat / Durdur kontrolü
- Geri sayım sırasında ekranın kilitlenmesini/uyumasını engelleme
- Süre dolduğunda otomatik `Enter` tuşu gönderimi
- Sade, koyu temalı arayüz (Tkinter)

## Gereksinimler

- Windows (uyku engelleme için `ctypes.windll` kullanır)
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

1. Saat, dakika ve saniye alanlarına istediğiniz süreyi girin.
2. **▶ Başlat** butonuna basın.
3. Geri sayım tamamlandığında uygulama otomatik olarak `Enter` tuşuna basar.
4. İstediğiniz an **■ Durdur** butonuyla geri sayımı iptal edebilirsiniz.

> Not: Uygulama, geri sayım bittiğinde etkin (aktif/odaklanmış) pencereye Enter tuşu gönderir. Enter'ın gitmesini istediğiniz pencerenin geri sayım bitmeden önce odakta (aktif) olduğundan emin olun.

## Lisans

Bu proje [MIT lisansı](LICENSE) ile lisanslanmıştır.
