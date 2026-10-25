"""English, Turkish and German strings, as on the website's donate section.

English is the default whatever the system locale; Turkish and German are
there for `maze-donate --lang=tr` / `--lang=de`. `t()` falls back to English,
then to the key.
"""
from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "tip_minimize": "Minimize",
        "tip_maximize": "Maximize / Restore",
        "tip_close": "Close",
        "eyebrow": "SUPPORT THE PROJECT",
        "hero_title": "Keep Maze Linux\nfree and independent.",
        "hero_sub": "Maze Linux is built independently — no company, no investors, "
                    "no ads, no telemetry. Every donation goes straight into the "
                    "project and helps take Maze Linux much further.",
        "point_1": "Build servers, mirrors and package repository hosting",
        "point_2": "Faster releases, more hardware testing and new features",
        "point_3": "Keeping Maze Linux free and independent for everyone",
        "costs": "Donations are used for server, domain and development costs.",
        "ok_title": "Signature verified",
        "ok_body": "These addresses were checked against the Maze Linux package key "
                   "on this computer, offline. Signed {date}.",
        "ok_updated": "Using the newer signed file you downloaded on this computer.",
        "bad_title": "Addresses not shown",
        "bad_body": "The signed address file did not verify ({why}), so Maze Donate "
                    "will not show any address. Do not donate to an address from a "
                    "copy you cannot verify — check the website instead.",
        "why_no_keyring": "the mazelinux-keyring package is missing",
        "why_no_gpgv": "gpgv is not installed",
        "why_bad_signature": "bad signature",
        "why_wrong_key": "signed by a different key",
        "why_not_signed": "not a signed file",
        "why_malformed": "unexpected content",
        "why_too_large": "file too large",
        "why_missing": "file missing",
        "why_older": "older than the one you have",
        "lbl_key": "SIGNING KEY",
        "btn_check": "Check for new addresses",
        "btn_checking": "Checking…",
        "btn_show_signed": "Show signed file",
        "btn_hide_signed": "Hide signed file",
        "btn_copy_signed": "Copy signed text",
        "btn_copy": "Copy address",
        "btn_copy_link": "Copy link",
        "btn_copy_cmd": "Copy commands",
        "btn_copied": "Copied",
        "btn_wallet": "Open in wallet",
        "btn_sponsors": "Open GitHub Sponsors",
        "pill_signed": "SIGNED",
        "pill_card": "PAY BY CARD",
        "xmr_note": "Private by default. Recommended.",
        "btc_note": "Native SegWit (bc1) address.",
        "sponsors_note": "Monthly or one-time, by card, through GitHub.",
        "paste_check": "After pasting, compare the first and last characters with the "
                       "address shown here — clipboard-swapping malware changes the middle "
                       "and hopes you only glance at it.",
        "check_none": "No change: the website's signed file is the one shown here.",
        "check_new": "New signed addresses found and verified. They are shown now.",
        "check_fail": "Could not check: {why}. The addresses shown are still the verified ones.",
        "check_net": "network error",
        "check_privacy": "Checking downloads one file from mazelinux.berkkucukk.com.tr. "
                         "Nothing is sent about you; it never runs on its own.",
        "verify_title": "VERIFY IT YOURSELF",
        "verify_maze": "On Maze Linux — the key ships in the mazelinux-keyring package",
        "verify_other": "On other systems — the fingerprint must match the one above",
        "wallet_fail": "No wallet is set to open {scheme}: links. Copy the address instead.",
        "src_bundled": "Signed file shipped with Maze Donate",
        "src_updated": "Signed file downloaded {date}",
        "thanks": "Thank you for supporting Maze Linux.",
        "website": "Donate page on the website",
    },
    "tr": {
        "tip_minimize": "Küçült",
        "tip_maximize": "Büyüt / Geri al",
        "tip_close": "Kapat",
        "eyebrow": "PROJEYİ DESTEKLE",
        "hero_title": "Maze Linux özgür ve\nbağımsız kalsın.",
        "hero_sub": "Maze Linux bağımsız olarak geliştiriliyor — şirket yok, yatırımcı "
                    "yok, reklam yok, telemetri yok. Her bağış doğrudan projeye gider "
                    "ve Maze Linux'u çok daha ileriye taşır.",
        "point_1": "Derleme sunucuları, yansılar ve paket deposu barındırma",
        "point_2": "Daha hızlı sürümler, daha fazla donanım testi ve yeni özellikler",
        "point_3": "Maze Linux'un herkes için özgür ve bağımsız kalması",
        "costs": "Bağışlar sunucu, alan adı ve geliştirme masraflarına harcanır.",
        "ok_title": "İmza doğrulandı",
        "ok_body": "Bu adresler bu bilgisayardaki Maze Linux paket anahtarıyla, "
                   "çevrimdışı olarak doğrulandı. İmza tarihi: {date}.",
        "ok_updated": "Bu bilgisayara indirdiğin daha yeni imzalı dosya kullanılıyor.",
        "bad_title": "Adresler gösterilmiyor",
        "bad_body": "İmzalı adres dosyası doğrulanamadı ({why}), bu yüzden Maze Donate "
                    "hiçbir adres göstermiyor. Doğrulayamadığın bir kopyadaki adrese "
                    "bağış yapma — web sitesine bak.",
        "why_no_keyring": "mazelinux-keyring paketi eksik",
        "why_no_gpgv": "gpgv kurulu değil",
        "why_bad_signature": "imza geçersiz",
        "why_wrong_key": "başka bir anahtarla imzalanmış",
        "why_not_signed": "imzalı bir dosya değil",
        "why_malformed": "beklenmeyen içerik",
        "why_too_large": "dosya çok büyük",
        "why_missing": "dosya yok",
        "why_older": "sendekinden daha eski",
        "lbl_key": "İMZA ANAHTARI",
        "btn_check": "Yeni adres var mı?",
        "btn_checking": "Kontrol ediliyor…",
        "btn_show_signed": "İmzalı dosyayı göster",
        "btn_hide_signed": "İmzalı dosyayı gizle",
        "btn_copy_signed": "İmzalı metni kopyala",
        "btn_copy": "Adresi kopyala",
        "btn_copy_link": "Bağlantıyı kopyala",
        "btn_copy_cmd": "Komutları kopyala",
        "btn_copied": "Kopyalandı",
        "btn_wallet": "Cüzdanda aç",
        "btn_sponsors": "GitHub Sponsors'u aç",
        "pill_signed": "İMZALI",
        "pill_card": "KARTLA ÖDE",
        "xmr_note": "Varsayılan olarak gizli. Önerilen.",
        "btc_note": "Native SegWit (bc1) adresi.",
        "sponsors_note": "Aylık ya da tek seferlik, kartla, GitHub üzerinden.",
        "paste_check": "Yapıştırdıktan sonra ilk ve son karakterleri buradaki adresle "
                       "karşılaştır — panoyu değiştiren zararlılar ortayı değiştirir ve "
                       "yalnızca göz atmanı umar.",
        "check_none": "Değişiklik yok: web sitesindeki imzalı dosya burada gösterilenle aynı.",
        "check_new": "Yeni imzalı adresler bulundu ve doğrulandı. Şimdi onlar gösteriliyor.",
        "check_fail": "Kontrol edilemedi: {why}. Gösterilen adresler hâlâ doğrulanmış olanlar.",
        "check_net": "ağ hatası",
        "check_privacy": "Kontrol, mazelinux.berkkucukk.com.tr adresinden tek bir dosya "
                         "indirir. Seninle ilgili hiçbir şey gönderilmez; kendiliğinden çalışmaz.",
        "verify_title": "KENDİN DOĞRULA",
        "verify_maze": "Maze Linux'ta — anahtar mazelinux-keyring paketiyle gelir",
        "verify_other": "Diğer sistemlerde — parmak izi yukarıdakiyle aynı olmalı",
        "wallet_fail": "{scheme}: bağlantılarını açacak bir cüzdan ayarlı değil. "
                       "Adresi kopyalayabilirsin.",
        "src_bundled": "Maze Donate ile gelen imzalı dosya",
        "src_updated": "{date} tarihinde indirilen imzalı dosya",
        "thanks": "Maze Linux'u desteklediğin için teşekkürler.",
        "website": "Web sitesindeki bağış sayfası",
    },
    "de": {
        "tip_minimize": "Minimieren",
        "tip_maximize": "Maximieren / Wiederherstellen",
        "tip_close": "Schließen",
        "eyebrow": "DAS PROJEKT UNTERSTÜTZEN",
        "hero_title": "Maze Linux frei und\nunabhängig halten.",
        "hero_sub": "Maze Linux wird unabhängig entwickelt — keine Firma, keine "
                    "Investoren, keine Werbung, keine Telemetrie. Jede Spende fließt "
                    "direkt in das Projekt und bringt Maze Linux viel weiter.",
        "point_1": "Build-Server, Spiegelserver und Hosting des Paket-Repositorys",
        "point_2": "Schnellere Releases, mehr Hardwaretests und neue Funktionen",
        "point_3": "Damit Maze Linux für alle frei und unabhängig bleibt",
        "costs": "Spenden werden für Server-, Domain- und Entwicklungskosten verwendet.",
        "ok_title": "Signatur geprüft",
        "ok_body": "Diese Adressen wurden offline mit dem Maze-Linux-Paketschlüssel auf "
                   "diesem Computer geprüft. Signiert am {date}.",
        "ok_updated": "Es wird die neuere signierte Datei verwendet, die du heruntergeladen hast.",
        "bad_title": "Keine Adressen angezeigt",
        "bad_body": "Die signierte Adressdatei ließ sich nicht prüfen ({why}), daher zeigt "
                    "Maze Donate keine Adresse an. Spende nicht an eine Adresse aus einer "
                    "Kopie, die du nicht prüfen kannst — sieh auf der Website nach.",
        "why_no_keyring": "das Paket mazelinux-keyring fehlt",
        "why_no_gpgv": "gpgv ist nicht installiert",
        "why_bad_signature": "ungültige Signatur",
        "why_wrong_key": "mit einem anderen Schlüssel signiert",
        "why_not_signed": "keine signierte Datei",
        "why_malformed": "unerwarteter Inhalt",
        "why_too_large": "Datei zu groß",
        "why_missing": "Datei fehlt",
        "why_older": "älter als die vorhandene",
        "lbl_key": "SIGNATURSCHLÜSSEL",
        "btn_check": "Nach neuen Adressen suchen",
        "btn_checking": "Wird geprüft…",
        "btn_show_signed": "Signierte Datei anzeigen",
        "btn_hide_signed": "Signierte Datei ausblenden",
        "btn_copy_signed": "Signierten Text kopieren",
        "btn_copy": "Adresse kopieren",
        "btn_copy_link": "Link kopieren",
        "btn_copy_cmd": "Befehle kopieren",
        "btn_copied": "Kopiert",
        "btn_wallet": "In Wallet öffnen",
        "btn_sponsors": "GitHub Sponsors öffnen",
        "pill_signed": "SIGNIERT",
        "pill_card": "PER KARTE",
        "xmr_note": "Standardmäßig privat. Empfohlen.",
        "btc_note": "Native-SegWit-Adresse (bc1).",
        "sponsors_note": "Monatlich oder einmalig, per Karte, über GitHub.",
        "paste_check": "Vergleiche nach dem Einfügen die ersten und letzten Zeichen mit der "
                       "hier gezeigten Adresse — Schadsoftware, die die Zwischenablage "
                       "austauscht, ändert die Mitte und hofft, dass du nur kurz hinsiehst.",
        "check_none": "Keine Änderung: Die signierte Datei der Website ist die hier gezeigte.",
        "check_new": "Neue signierte Adressen gefunden und geprüft. Sie werden jetzt angezeigt.",
        "check_fail": "Prüfung nicht möglich: {why}. Die angezeigten Adressen sind weiterhin die geprüften.",
        "check_net": "Netzwerkfehler",
        "check_privacy": "Die Prüfung lädt eine Datei von mazelinux.berkkucukk.com.tr. "
                         "Es wird nichts über dich gesendet; sie läuft nie von selbst.",
        "verify_title": "SELBST PRÜFEN",
        "verify_maze": "Unter Maze Linux — der Schlüssel kommt mit dem Paket mazelinux-keyring",
        "verify_other": "Auf anderen Systemen — der Fingerabdruck muss mit dem obigen übereinstimmen",
        "wallet_fail": "Keine Wallet ist für {scheme}:-Links eingerichtet. Kopiere stattdessen die Adresse.",
        "src_bundled": "Mit Maze Donate ausgelieferte signierte Datei",
        "src_updated": "Am {date} heruntergeladene signierte Datei",
        "thanks": "Danke, dass du Maze Linux unterstützt.",
        "website": "Spendenseite auf der Website",
    },
}

_lang = "en"


def set_language(lang: str) -> None:
    global _lang
    if lang in STRINGS:
        _lang = lang


def language() -> str:
    return _lang


def t(key: str, **kw) -> str:
    s = STRINGS.get(_lang, {}).get(key) or STRINGS["en"].get(key) or key
    return s.format(**kw) if kw else s
