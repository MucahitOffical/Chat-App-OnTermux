import socket
import threading
import re 
from Logger import process_message, log_message, save_data
from Authorize import user_saver, login_user
from UserId import Person



def broadcast(message, sender = None, usname="Anonim_User", event="CHAT"):

    msg = message.decode(
        "utf-8",
        errors="ignore"
    )

    with client_lock:
        current_clients = list(clients.keys())

    for client in current_clients:
        
        if client == sender:
            continue

        try:
            client.send(message)

        except OSError:
            with client_lock:
                clients.pop(client, None)

            try:
                client.close()
            except OSError:
                pass


    log_message(
        usname,
        msg,
        event
    )


def handle_client(conn, addr):

    person = clients[conn]
    print(f"{person.username} bağlandı")

    while True:

        try:
            msg = conn.recv(1024)

            if not msg:
                log_message(person.username, "Bağlantı kesildi", event="LEAVE")
                break

            message = msg.decode(
                "utf-8",
                errors="ignore"
            )

            if message.lower().startswith("/update"):
                update_data = message.split(" ")

                if len(update_data) < 3:
                    conn.send(
                        "Eksik parametre girildi. Kullanım: /update <field> <new_value>".encode()
                    )
                    continue

                if len(update_data) > 3:
                    conn.send(
                        "Fazla parametre girildi. Kullanım: /update <field> <new_value>".encode()
                    )
                    continue

                if update_data[1].lower() not in ["username", "email", "password", "occupation"]:
                    conn.send("Geçersiz güncelleme alanı.".encode())
                    continue

                if update_data[1].lower() == "username":
                    old_username = person.username

                    update = person.update(username=update_data[2])

                    log_message(
                        person.username,
                        f"{old_username} updated {update_data[1]} to {update_data[2]}",
                        event="UPDATE"
                    )

                    conn.send(f"{update}".encode())
                    continue

                if update_data[1].lower() == "email":
                    update = person.update(email=update_data[2])
                    conn.send(f"{update}".encode())

                if update_data[1].lower() == "password":
                    update = person.update(password=update_data[2])
                    conn.send(f"{update}".encode())

                if update_data[1].lower() == "occupation":
                    update = person.update(occupation=update_data[2])
                    conn.send(f"{update}".encode())

                log_message(
                    person.username,
                    f"{person.username} updated {update_data[1]} to {update_data[2]}",
                    event="UPDATE"
                )

            if message.lower() == "exit":

                broadcast(
                    f"{person.username} çıktı".encode(),
                    usname=person.username,
                    event="EXIT"
                )
                break

            print(f"{person.username}: {message}")

            broadcast(f"{person.username}: {message}".encode(),
                sender=conn,
                usname=person.username
            )

            process_message(message)


        except Exception as e:
            print("Hata:", e)
            break

    with client_lock:
        if conn in clients:
            del clients[conn]

    conn.close()

    print(person.username, "ayrıldı")
#------------------------------------------------------------------------------------------------

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("0.0.0.0", 5555))
server.listen()
server.settimeout(1.0)

clients = {}
client_lock = threading.Lock()

DataUserPath = "DataBase/UserList.xlsx"

try:
    while True:

        try:
            conn, addr = server.accept()
            conn_user = None
            command = conn.recv(1024).decode()

            if command.startswith("REGISTER:"):    
                result, data = user_saver(command, addr[0])
                            
                if result:
                    conn_user = data
                    conn.send(f"REGISTER_OK:{conn_user.username}:{conn_user.token}".encode())
                else:
                    runCont = True
                    while runCont:
                        conn.send(f"REGISTER_FAIL:{data}".encode())

                        usData = conn.recv(1024)

                        if not usData:
                            conn.close()
                            runCont = False
                            break

                        usData = usData.decode()
                        
                        result, data = user_saver(usData, addr[0])

                        if result:
                            conn_user = data
                            conn.send(
                                f"REGISTER_OK:{conn_user.username}:{conn_user.token}".encode()
                            )
                            runCont = False

            else:

                ok, conn_user = login_user(conn, command)

                if not ok:
                    continue
            
        except socket.timeout:
            continue

        if conn_user is None:
            continue

        conn_user.addr = addr[0]

        with client_lock:
            clients[conn] = conn_user

        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        )

        thread.start()


except KeyboardInterrupt:
    print("\nSunucu kapatılıyor...")
    save_data()

    with client_lock:
        current_clients = list(clients.keys())

    for client in current_clients:
        try:
            client.close()
        except:
            pass

    server.close()