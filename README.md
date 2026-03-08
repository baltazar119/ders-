# YTÜ Online Ders Otomasyonu (Ders Linki Tabanlı)

Bu proje, her ders için sabit `lesson_url` sayfasına gidip ders saatinde oluşan **"Derse Katıl" / Zoom** bağlantısını otomatik açar.

---

## 0) Çok önemli güvenlik notu

- Bu repo **public** olduğu için kullanıcı adı/şifreyi **asla** GitHub'a yazma.
- Sadece telefondaki veya bilgisayardaki yerel `.env` dosyasına yaz.
- `.env` zaten `.gitignore` içinde, yani commit edilmez.
- Hesap bilgilerini daha önce paylaştıysan şifreni hemen değiştir.

---

## 1) Hangi dosyaya ne yazacağım? (kısa cevap)

- **Kullanıcı adı + şifre:** `.env`
- **Ders gün/saat/link:** `timetable.yaml`
- **Kod dosyası:** `auto_join.py` (dokunmana gerek yok)

---

## 2) Bilgisayarda ilk kurulum (tek sefer)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
```

### 2.1 `.env` içine yazılacak örnek

`.env` dosyasını aç ve doldur:

```env
ONLINE_USERNAME=mail_or_username
ONLINE_PASSWORD=your_password
CHECK_INTERVAL_SECONDS=30
JOIN_EARLY_MINUTES=10
JOIN_POLL_SECONDS=15
LESSON_WAIT_TIMEOUT_MINUTES=45
HEADLESS=false
```

> `HEADLESS=false` iken tarayıcıyı görürsün (debug için iyi). Sorunsuz çalışınca `true` yapabilirsin.

### 2.2 `timetable.yaml` içine yazılacak format

Her ders için bu 5 alan zorunlu:

```yaml
courses:
  - name: Ders Adı
    day: monday
    start_time: "09:00"
    end_time: "10:50"
    lesson_url: "https://online.yildiz.edu.tr/?transaction=..."
```

Gün değerleri sadece şunlar olmalı:
- `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`

### 2.3 Çalıştırma

```bash
source .venv/bin/activate
python auto_join.py
```

Akış:
1. Giriş yapar.
2. O an aktif ders penceresinde mi diye bakar.
3. O dersin `lesson_url` sayfasına gider.
4. "Derse Katıl"/Zoom linkini bulunca açar.
5. Aynı dersi aynı gün ikinci kez açmaz.

---

## 3) Android telefona "uygulama gibi" kurulum (en net yöntem)

> Gerçekte native APK değil; Termux içinde çalışan script. Ama ana ekrandan tek dokunuşla açılacak şekilde kurabiliriz.

### 3.1 Gerekli uygulamalar

- **Termux**
- (Opsiyonel ama önerilen) **Tasker** veya **Termux:Widget**

### 3.2 Termux içinde adım adım (sırasıyla)

```bash
pkg update -y
pkg install -y python git
git clone <GITHUB_REPO_URL>
cd <REPO_KLASORU>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
```

Sonra:
1. `nano .env` ile kullanıcı adı/şifreyi yaz.
2. `nano timetable.yaml` ile ders programını yaz.
3. Test için çalıştır:

```bash
source .venv/bin/activate
python auto_join.py
```

### 3.3 Ana ekrana "uygulama gibi" kısayol

#### Seçenek A — Termux:Widget (kolay)
1. Repo klasöründe `start.sh` oluştur:

```bash
#!/data/data/com.termux/files/usr/bin/bash
cd <REPO_KLASORU>
source .venv/bin/activate
python auto_join.py
```

2. Çalıştırılabilir yap:

```bash
chmod +x start.sh
```

3. `start.sh` dosyasını `~/.shortcuts/` altına kopyala (Termux:Widget bunu görür).
4. Ana ekrana Termux widget ekle, `start.sh` tek dokunuşla çalışsın.

#### Seçenek B — Tasker (zamanlayıcı)
- Tasker'da saat bazlı profil oluşturup şu komutu çalıştır:

```bash
cd <REPO_KLASORU> && source .venv/bin/activate && python auto_join.py
```

> Android pil optimizasyonunda Termux/Tasker için "kısıtlama yok" ayarı vermezsen arka planda durabilir.

---

## 4) iPhone/iPad gerçeği (önemli)

iOS'ta Playwright otomasyonunu telefon içinde sürekli çalıştırmak pratik değil.

En stabil yöntem:
1. Scripti bilgisayar veya VPS'te 7/24 çalıştır.
2. Telefona bildirim (Telegram/Discord) gönder.
3. Gerekirse Zoom'u telefondan aç.

---

## 5) Sık yapılan hatalar

- Saat formatını `9.00` yazmak → **yanlış**, `09:00` olmalı.
- `day` alanına `Pazartesi` yazmak → **yanlış**, `monday` olmalı.
- Linkin sonuna boşluk/ek karakter bırakmak → bulunamama sorunu olur.
- `.env` dosyasını yanlış klasöre koymak → script kullanıcı adı/şifreyi göremez.

---

## 6) Otomatik başlatma (Linux/PC için)

```ini
# ~/.config/systemd/user/ytu-autojoin.service
[Unit]
Description=YTU Auto Join

[Service]
Type=simple
WorkingDirectory=/path/to/repo
ExecStart=/path/to/repo/.venv/bin/python /path/to/repo/auto_join.py
Restart=always
RestartSec=15

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now ytu-autojoin.service
```
