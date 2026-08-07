import uuid
import unicodedata
import re

class Message():
    def __init__(self, sender, content, timestamp):
        self.id = uuid.uuid4().hex
        self.sender = sender
        self.content = content
        self.timestamp = timestamp

    @staticmethod
    def content_clean(metin):
        degisim = {
            "@": "a",
            "0": "o",
            "1": "i",
            "3": "e",
            "$": "s",
            "5": "s",
            "7": "t"
        }

        # Küçük harf
        metin = metin.lower()

        # Karakter değişimleri
        for eski, yeni in degisim.items():
            metin = metin.replace(eski, yeni)

        # Aksan temizleme
        metin = unicodedata.normalize("NFKD", metin)
        metin = "".join(
            c for c in metin
            if not unicodedata.combining(c)
        )

        # Harf dışındakileri sil
        metin = re.sub(r"[^a-z\s]", "", metin)

        # Fazla boşlukları temizle
        metin = " ".join(metin.split())

        return metin

    
    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "content": self.content,
            "timestamp": self.timestamp
        }