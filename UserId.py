import uuid
import pandas as pd

class Person():

    def __init__(self, username, email, password, token, addr, location, Occupation = "",degree="Member"):
        self.id = uuid.uuid4().hex
        self.username = username
        self.email = email
        self.degree = degree
        self.password = password
        self.token = token
        self.addr = addr
        self.location = location
        self.Occupation = Occupation

    def user_frame(self):
        data = self.__dict__.copy()
        data.pop("id")
        return pd.DataFrame(index=[self.id], data=[data])

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)