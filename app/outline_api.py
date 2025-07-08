import client
import asyncio

# Подсчёт в гигабайтах
def gb_to_bytes (gb: float):
    bytes_in_gb = 1000**3
    return int(gb*bytes_in_gb)



def create_access_key(key_id:str = None, name: str = None, data_limit_gb: float = None):
    return client.create_key(key_id = key_id, name=name, data_limit=gb_to_bytes(data_limit_gb))

def delete_access_key(key_id:str):
    return client.delete_key(key_id)

def rename_access_key(key_id:str):
    return client.rename_key(key_id)

def get_access_key_url(key_id:str):
    return client.get_key(key_id)


# Получение информации по серверу
def get_keys():
    client.get_key()

def get_key_info(key_id:str):
    return client.get_key(key_id)

def get_service_info():
    return client.get_server_information()

