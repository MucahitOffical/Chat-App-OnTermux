import os
import hashlib
import secrets
import pandas as pd
import threading
from MailEvents import sendMail, mailControl
from Logger import log_message
from UserId import Person
from IpEvents import IpInfo

path = "DataBase/UserList.xlsx"

register_lock = threading.Lock()


def register_user(new_user, addr):

    with register_lock:

        os.makedirs("DataBase", exist_ok=True)

        if not os.path.exists(path) or os.path.getsize(path) == 0:
            df = pd.DataFrame()
            
            df.to_excel(path, index=False)

        userdf = pd.read_excel(path)

        # Kullanıcı adı kontrolü
        if new_user["User"] in userdf["User"].values:
            return False, "Bu kullanıcı adı zaten kullanılıyor."

        # E-posta kontrolü
        if new_user["E-Mail"] in userdf["E-Mail"].values:
            return False, "Bu e-posta zaten kayıtlı."

        # E-posta doğrulama kontrolü
        ok = mailControl(new_user["E-Mail"])
        if not ok:    
            return False, "Mail gönderilemedi. Lütfen geçerli bir e-posta adresi girin."

        hashed_password = hashlib.sha256(
            new_user["Pasw"].encode("utf-8")
        ).hexdigest()

        token = secrets.token_hex(32)

        try:
            ip_info = IpInfo(ip=addr).get_ip_info()
            location = ip_info.get("city", "Unknown")
        except Exception:
            location = "Unknown"

        new_person = Person(
            username=new_user["User"],
            email=new_user["E-Mail"],
            password=hashed_password,
            token=token,
            addr=addr,
            location=location,
            )

        userdf = pd.concat(
            [userdf, new_person.user_frame()],
            ignore_index=True
        )

        userdf.to_excel(path, index=False)

        log_message(
            new_user["User"],
            f"{new_user['User']} kayıt oldu.",
            event="REGISTER"
            )
        
        return True, new_person


def user_Controller(usInfo):

    alldata = pd.read_excel(path)

    # Kullanıcı var mı?
    if usInfo["User"] not in alldata["User"].values:
        return False, "USER_FAIL:Lütfen kayıt olun."

    # Kullanıcının satırını al
    user_information = Person(alldata.loc[
        alldata["User"] == usInfo["User"]
    ].iloc[0])

    # Girilen şifreyi hashle
    hashed_password = hashlib.sha256(
        usInfo["Password"].encode("utf-8")
    ).hexdigest()

    # Şifre doğru mu?
    if hashed_password == user_information.password:
        return True, user_information

    return False, "PASW_FAIL:Gelen kodu girin. "


def user_saver(command, addr):

    command = command.split(":")

    user_dict = {
        "User": command[1],
        "E-Mail": command[2],
        "Pasw": command[3]
    }

    result, data = register_user(user_dict, addr)

    return result, data


def findUserByToken(utoken):

    aldata = pd.read_excel(path)

    userData = aldata.loc[aldata["Token"] == utoken]

    if userData.empty:
        return None

    new_user = Person(userData.iloc[0])
    
    return new_user


def login_user(conn, command):

    user = findUserByToken(command)
    if user is not None:

        conn.send(f"LOGIN_OK:{user.username}".encode())

        log_message(
            user.username,
            f"{user.username} giriş yaptı.",
            event="LOGIN"
            )
        
        return True, user
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

        user = result[1]

        conn.send(
            f"LOGIN_OK:{user.username}:{user.token}".encode()
        )

        log_message(
            user.username,
            f"{user.username} giriş yaptı.",
            event="LOGIN"
            )
        
        return True, user
    #------------------------------------------------------------------------------------
    shortData = result[1].split(":")[0]

    if shortData == "USER_FAIL":

        conn.send(
            f"LOGIN_FAIL:Kayıtlı değilsiniz lütfen kayıt olun!:{shortData}".encode()
        )

        return False, None

    if shortData == "PASW_FAIL":

        all_data = pd.read_excel(path)

        user = Person(all_data.loc[
            all_data["User"] == lc_list[1]
        ].iloc[0])

        ok, mail_code = sendMail(user.email)

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
                    f"LOGIN_OK:{user.username}:{user.token}".encode()
                )

                log_message(
                    user.username,
                    f"{user.username} giriş yaptı.",
                    event="LOGIN"
                    )

                return True, user

        except ValueError:
            pass

        conn.send("LOGIN_FAIL:".encode())

    return False, None