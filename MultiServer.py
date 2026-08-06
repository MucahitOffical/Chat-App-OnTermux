import socket
import threading
from Logger import process_message, log_message, save_data
from Authorize import user_saver, login_user



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

    username = clients[conn]["User"]
    print(f"{username} bağlandı")

    while True:

        try:
            msg = conn.recv(1024)

            if not msg:
                log_message(username, "Bağlantı kesildi", event="LEAVE")
                break

            message = msg.decode(
                "utf-8",
                errors="ignore"
            )

            if message.lower() == "exit":

                broadcast(
                    f"{username} çıktı".encode(),
                    usname=username,
                    event="EXIT"
                )
                break

            print(f"{username}: {message}")

            broadcast(f"{username}: {message}".encode(),
                sender=conn,
                usname=username
            )

            process_message(message)


        except Exception as e:
            print("Hata:", e)
            break

    with client_lock:
        if conn in clients:
            del clients[conn]

    conn.close()

    print(username, "ayrıldı")
#------------------------------------------------------------------------------------------------

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("0.0.0.0", 5000))
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
                result, data = user_saver(command)
                            
                if result:
                    conn_user = data
                    conn.send(f"REGISTER_OK:{conn_user['User']}:{conn_user['Token']}".encode())
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
                        
                        result, data = user_saver(usData)

                        if result:
                            conn_user = data
                            conn.send(
                                f"REGISTER_OK:{conn_user['User']}:{conn_user['Token']}".encode()
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

        conn_user["Addr"] = addr

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