import os
import hashlib
import secrets
import pandas as pd
import threading
from MailJob import sendMail
from Logger import log_message

path = "DataBase/UserList.xlsx"

register_lock = threading.Lock()


def register_user(new_user):

    with register_lock:

        os.makedirs("DataBase", exist_ok=True)

        if not os.path.exists(path) or os.path.getsize(path) == 0:
            df = pd.DataFrame(
                columns=["User", "E-Mail", "Pasw", "Token"]
            )
            df.to_excel(path, index=False)

        userdf = pd.read_excel(path)

        # Kullanıcı adı kontrolü
        if new_user["User"] in userdf["User"].values:
            return False, "Bu kullanıcı adı zaten kullanılıyor."

        # E-posta kontrolü
        if new_user["E-Mail"] in userdf["E-Mail"].values:
            return False, "Bu e-posta zaten kayıtlı."

        hashed_password = hashlib.sha256(
            new_user["Pasw"].encode("utf-8")
        ).hexdigest()

        token = secrets.token_hex(32)

        newdf = pd.DataFrame([{
            "User": new_user["User"],
            "E-Mail": new_user["E-Mail"],
            "Pasw": hashed_password,
            "Token": token
        }])

        userdf = pd.concat(
            [userdf, newdf],
            ignore_index=True
        )

        userdf.to_excel(path, index=False)

        log_message(
            new_user["User"],
            f"{new_user['User']} giriş yaptı.",
            event="REGISTER"
            )
        
        return True, {
            "User": new_user["User"],
            "E-Mail": new_user["E-Mail"],
            "Token": token
        }


def user_Controller(usInfo):

    alldata = pd.read_excel(path)

    # Kullanıcı var mı?
    if usInfo["User"] not in alldata["User"].values:
        return False, "USER_FAIL:Lütfen kayıt olun."

    # Kullanıcının satırını al
    user_information = alldata.loc[
        alldata["User"] == usInfo["User"]
    ].iloc[0]

    # Girilen şifreyi hashle
    hashed_password = hashlib.sha256(
        usInfo["Password"].encode("utf-8")
    ).hexdigest()

    # Şifre doğru mu?
    if hashed_password == user_information["Pasw"]:
        return True, user_information["Token"]

    return False, "PASW_FAIL:Gelen kodu girin. "


def user_saver(command):

    command = command.split(":")

    user_dict = {
        "User": command[1],
        "E-Mail": command[2],
        "Pasw": command[3]
    }

    result, data = register_user(user_dict)

    return result, data


def findUser(utoken):

    aldata = pd.read_excel(path)

    userData = aldata.loc[aldata["Token"] == utoken]

    if userData.empty:
        return None

    return userData.iloc[0]


def login_user(conn, command):

    user = findUser(command)
    if user is not None:

        conn.send(f"LOGIN_OK:{user['User']}".encode())

        log_message(
            user["User"],
            f"{user['User']} giriş yaptı.",
            event="LOGIN"
            )
        
        return True, {
            "User": user["User"],
            "E-Mail": user["E-Mail"],
            "Token": user["Token"]
        }
    #------------------------------------------------------------------------------------

    conn.send("LOGIN_FAIL:".encode())

    last_chance = conn.recv(1024)

    if not last_chance:
        return False, None

    lc_list = last_chance.decode().split(":")

    login_data = {
        "User": lc_list[1],
        "Password": lc_list[2]
    }

    result = user_Controller(login_data)

    if result[0]:

        all_data = pd.read_excel(path)

        user = all_data.loc[
            all_data["Token"] == result[1]
        ].iloc[0]

        conn.send(
            f"LOGIN_OK:{user['User']}:{user['Token']}".encode()
        )

        log_message(
            user["User"],
            f"{user['User']} giriş yaptı.",
            event="LOGIN"
            )
        
        return True, {
            "User": user["User"],
            "E-Mail": user["E-Mail"],
            "Token": user["Token"]
        }
    #------------------------------------------------------------------------------------
    shortData = result[1].split(":")[0]

    if shortData == "USER_FAIL":

        conn.send(
            f"LOGIN_FAIL:Kayıtlı değilsiniz lütfen kayıt olun!:{shortData}".encode()
        )

        return False, None

    if shortData == "PASW_FAIL":

        all_data = pd.read_excel(path)

        user = all_data.loc[
            all_data["User"] == lc_list[1]
        ].iloc[0]

        ok, mail_code = sendMail(user["E-Mail"])

        if not ok:

            conn.send("MAIL_FAIL".encode())
            return False, None

        conn.send(
            f"LOGIN_FAIL:Kayıtlısınız fakat şifre yanlış. Mail kodunu giriniz:{shortData}".encode()
        )

        code = conn.recv(1024)

        if not code:
            return False, None

        try:

            if int(code.decode()) == mail_code:

                conn.send(
                    f"LOGIN_OK:{user['User']}:{user['Token']}".encode()
                )

                log_message(
                    user["User"],
                    f"{user['User']} giriş yaptı.",
                    event="LOGIN"
                    )

                return True, {
                    "User": user["User"],
                    "E-Mail": user["E-Mail"],
                    "Token": user["Token"]
                }

        except ValueError:
            pass

        conn.send("LOGIN_FAIL:".encode())

    return False, None