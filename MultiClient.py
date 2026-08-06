import socket
import threading
import os
import re
from getpass import getpass
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

HOST = "Server IP Adresi"
PORT = 5000


def receive_messages(sock):

    while True:
        try:
            data = sock.recv(1024)

            if not data:
                print("Sunucu bağlantıyı kapattı.")
                break

            message = data.decode("utf-8", errors="ignore")
            print(f"\n{message}")

        except:
            print("Bağlantı kesildi.")
            break


def nickNameCont(nickname):

    # Harf dışındakileri sil
    nickname = re.sub(r"[^a-zA-ZçğıöşüÇĞİÖŞÜ\s]", "", nickname)

    # Fazla boşlukları temizle
    nickname = " ".join(nickname.split())

    return nickname


def mail_kontrol(mail):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, mail))


def check_user():

    print("\n=== Kullanıcı Kayıt ===\n")

    while True:
        username = input("Kullanıcı Adı: (Boşluk ve harf dışı itemler silinecektir. 12 haneden fazla olmamalı.) ").strip()

        username = nickNameCont(username)

        if username:
            if len(username) >= 12:
                print("Kullanıcı adı 12 haneden fazla! ")
            else:
                break

        print("Kullanıcı adı boş bırakılamaz.\n")

    while True:
        email = input("E-Mail: ").strip()

        if email:
            if mail_kontrol(email) == True:
                break
            else:
                print("Hatalı e-mail.")

        print("E-Mail boş bırakılamaz.\n")

    while True:
        password = getpass("Şifre: (Şifre : içermez) ").strip()

        if password:
            if ":" in password:
                print("Şifrede : kullanılamaz.")
            else:
                break

        print("Şifre boş bırakılamaz.\n")

    return {
        "User": username,
        "E-Mail": email,
        "Password": password
    }


def logUser():

    print("\n=== Kullanıcı Sorgu ===\n")

    while True:
        username = input("Kullanıcı Adı: (Boşluk ve harf dışı itemler silinecektir.) ").strip()

        username = nickNameCont(username)

        if username:
            break

        print("Kullanıcı adı boş bırakılamaz.\n")


    while True:
        password = getpass("Şifre: (Şifre : içermez) ").strip()

        if password:
            if ":" in password:
                print("Şifrede : kullanılamaz.")
            else:
                break

        print("Şifre boş bırakılamaz.\n")

    return username, password


def register(client):

    while True:

        new_user = check_user()

        client.send(
            f"REGISTER:{new_user['User']}:{new_user['E-Mail']}:{new_user['Password']}".encode()
        )

        command = client.recv(1024).decode().split(":")

        if command[0] == "REGISTER_OK":

            print(f"Hello {command[1]}")

            with open("Token.txt", "w") as f:
                f.write(command[2])

            return

        print(command[1])


# -------------------------------------------------------------------

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# -------------------------------------------------------------------

if os.path.isfile("Token.txt"):

    with open("Token.txt", "r") as f:
        token = f.read().strip()
        client.send(token.encode())

    command = client.recv(1024).decode().split(":", 1)

    if command[0] == "LOGIN_OK":
        username = command[1]
        print(f"Merhaba {username}, çıkmak için 'exit' yazabilirsin.\n")

    elif command[0] == "LOGIN_FAIL":
        username, password = logUser()
        client.send(f"LOGIN_FAIL:{username}:{password}".encode())

        answer = client.recv(1024).decode().split(":")

        if answer[0] == "LOGIN_OK":
            with open("Token.txt","w", encoding="utf-8") as f:
                f.write(answer[2])
            username = answer[1]
            print(f"Merhaba {username}, çıkış için exit yazabilirsiniz.\n")

        elif answer[0] == "LOGIN_FAIL":
            if answer[2] == "USER_FAIL":
                print(answer[1])
                register(client)
            if answer[2] == "PASW_FAIL":
                parİnp = input(f"{answer[1]} Gelen e-postayı girin lütfen. ")
                client.send(parİnp.encode()) 
                resultİn = client.recv(1024).decode().split(":")
                if resultİn[0] == "LOGIN_OK":
                    username = resultİn[1]
                    print(f"Merhaba {username}, çıkmak için 'exit' yazabilirsin.\n")
                    with open("Token.txt","w", encoding="utf-8") as f:
                        f.write(resultİn[2])
                else:
                    register(client)
else:
    register(client)

# -------------------------------------------------------------------

thread = threading.Thread(
    target=receive_messages,
    args=(client,),
    daemon=True
)

thread.start()

# -------------------------------------------------------------------

session = PromptSession()

while True:

    try:
        with patch_stdout():
            message = session.prompt(f"{username}> ")

        client.send(message.encode())

        if message.lower() == "exit":
            break

    except KeyboardInterrupt:
        client.send("exit".encode("utf-8"))
        break

    except Exception as e:
        print(e)
        break

client.close()