import uuid
import pandas as pd
import hashlib

path = "DataBase/UserList.xlsx"

class Person():

    def __init__(self, username, email, password, token, addr, location, occupation = "",degree="Member"):
        self.id = uuid.uuid4().hex
        self.username = username
        self.email = email
        self.degree = degree
        self.password = password
        self.token = token
        self.addr = addr
        self.location = location
        self.occupation = occupation

    def user_frame(self):
        data = self.__dict__.copy()
        data.pop("id")
        return pd.DataFrame(index=[self.id], data=[data])

    def update(self, **kwargs):
        df = pd.read_excel(path, index_col=0)

        for key, value in kwargs.items():

            if key == "username":
                if value in df["username"].values:
                    return "Bu kullanıcı adı zaten mevcut."

            elif key == "email":
                if value in df["email"].values:
                    return "Bu e-posta zaten mevcut."

            elif key == "password":
                value = hashlib.sha256(
                    value.encode("utf-8")
                ).hexdigest()

                df.loc[self.id, "password"] = value
                df.to_excel("users.xlsx")

            setattr(self, key, value)
            df.loc[self.id, key] = value
            df.to_excel("users.xlsx")
        return "İşlem başarılı."