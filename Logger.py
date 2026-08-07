import os
from datetime import datetime
from collections import Counter
import threading
import pandas as pd
from MessageEvents import Message

lock = threading.Lock()
word_count = Counter()
current_day = datetime.now().strftime("%Y-%m-%d")

def process_message(msg):

    global current_day

    today = datetime.now().strftime("%Y-%m-%d")

    with lock:

        if today != current_day:

            save_data(current_day)

            word_count.clear()
            current_day = today


        words = msg.split()

        for word in words:

            cleaned = Message.content_clean(word)

            if cleaned:
                word_count[cleaned] += 1


def log_message(username, message, event="CHAT"):
    # Klasör yoksa oluştur
    os.makedirs("DataBase/ChatLog", exist_ok=True)

    filtime = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(
        f"DataBase/ChatLog/chat_log_{filtime}.txt",
        "a",
        encoding="utf-8"
    ) as f:
        f.write(f"[{time}] [{event}] {username}: {message}\n")
        

def save_data(date=None):

    folder = "DataBase/WordLog"
    os.makedirs(folder, exist_ok=True)

    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")

    filename = f"{date}.xlsx"
    filepath = os.path.join(folder, filename)

    df = pd.DataFrame(
        word_count.items(),
        columns=["Word", "Repeat"]
    )

    if os.path.exists(filepath):
        existing_df = pd.read_excel(filepath)

        df = (
            pd.concat([existing_df, df])
            .groupby("Word", as_index=False)["Repeat"]
            .sum()
        )

    df.to_excel(filepath, index=False)

    print("\nKelime verileri kaydedildi.\n")
    print(df)