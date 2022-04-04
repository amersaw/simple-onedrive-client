import os

from simple_onedrive_client.client import SimpleOneDriveClient


def dump_token_to_file(new_token: str):
    with open("token.json", "w") as f:
        f.write(new_token)


client = SimpleOneDriveClient(
    client_id="",
    secret="",
    token_updated=dump_token_to_file,
)
if os.path.exists("token.json"):
    with open("token.json", "r") as f:
        client.load_auth(token_fn="token.json")
print(client.local_login())

client.upload_file(
    "amer.jpg",
    r"C:\Users\wizamer\Desktop\amer.jpg",
    one_drive_dest_path="/TheCloud/",
)
