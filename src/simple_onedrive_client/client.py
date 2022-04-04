from __future__ import annotations

import json
import os
import time
import webbrowser
from urllib.parse import parse_qs, quote, urlparse

import jwt
import requests

from simple_onedrive_client.callback_http_listner import CallbackHttpListner


class SimpleOneDriveClient:
    FULL_WRITE_ACCESS_SCOPE = (
        "openid offline_access https://graph.microsoft.com/Files.ReadWrite.All"
    )

    def __init__(
        self,
        *,
        client_id: str,
        secret: str,
        redirect_url: str = None,
        full_write: bool = True,
        token_updated=None,
    ) -> None:
        self.client_id = client_id
        self.secret = secret
        self.redirect_url = redirect_url or "http://localhost:7700/callback"
        self.token_updated = token_updated
        self.auth = None
        pass

    def get_login_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_url,
            "scope": SimpleOneDriveClient.FULL_WRITE_ACCESS_SCOPE,
        }

        params_str = "&".join([f"{k}={quote(v)}" for k, v in params.items()])
        return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{params_str}"

    def refresh_token(self):
        if self.get_token_payload()["exp"] < time.time():
            print("Refreshing token")
            resp = requests.post(
                url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.secret,
                    "response_type": "code",
                    "redirect_uri": self.redirect_url,
                    "grant_type": "refresh_token",
                    "refresh_token": self.auth["refresh_token"],
                },
            )
            print("Refreshing token done")
            self.auth = resp.json()
            if self.token_updated:
                self.token_updated(self.dumps())
        else:
            print("Token is still valid")

    def complete_login_using_code(self, code):
        resp = requests.post(
            url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.secret,
                "response_type": "code",
                "redirect_uri": self.redirect_url,
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        resp.raise_for_status()

        self.auth = resp.json()
        if self.auth["token_type"] != "Bearer":
            raise Exception("Invalid token type")
        if self.token_updated:
            self.token_updated(self.dumps())

    def get_token_payload(self):
        if self.auth:
            return jwt.decode(
                self.auth["id_token"],
                options={"verify_signature": False},
                verify=False,
            )
        return None

    def local_login(self) -> bool:
        if self.auth is not None:
            self.refresh_token()
            return True
        self.redirect_url = "http://localhost:7700/callback"
        login_url = self.get_login_url()
        webbrowser.open_new_tab(login_url)
        callback_url = CallbackHttpListner.listen_till_callback_received()

        parsed_url = urlparse(callback_url)
        code = parse_qs(parsed_url.query)["code"][0]
        token = self.complete_login_using_code(code)
        print(token)
        return True

    def load_auth(self, token_fn: str)->bool:
        try:
            with open(token_fn, "r") as f:
                self.auth = json.loads(f.read())
                self.refresh_token()
                return True
        except:
            self.auth = None
        return False

    def dumps(self):
        return json.dumps(self.auth)

    def upload_file(self, file_name, file_full_path, one_drive_dest_path="/"):
        """
        Uploads a file to OneDrive.
        Credits goes to : https://github.com/jsnm-repo/Python-OneDriveAPI-FileUpload
        :param file_name: The name of the file to upload.
        :param file_full_path: The full path to the file to upload.
        :param one_drive_dest_path: The path to the folder to upload the file to.
        :return:
        """
        base_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{one_drive_dest_path}{file_name}"
        file_size = os.stat(file_full_path).st_size
        headers = {"Authorization": "Bearer {}".format(self.auth["access_token"])}
        if file_size < 4100000:
            with open(file_full_path, "rb") as file_data:
                # Perform is simple upload to the API
                r = requests.put(
                    f"{base_url}:/content",
                    data=file_data,
                    headers=headers,
                )
            return r.json()
        else:
            # Creating an upload session
            upload_session = requests.post(
                f"{base_url}:/createUploadSession",
                headers=headers,
            ).json()

            with open(file_full_path, "rb") as f:
                total_file_size = os.path.getsize(file_full_path)
                chunk_size = 327680
                chunk_number = total_file_size // chunk_size
                chunk_leftover = total_file_size - chunk_size * chunk_number
                i = 0
                while True:
                    chunk_data = f.read(chunk_size)
                    start_index = i * chunk_size
                    end_index = start_index + chunk_size
                    # If end of file, break
                    if not chunk_data:
                        break
                    if i == chunk_number:
                        end_index = start_index + chunk_leftover
                    # Setting the header with the appropriate chunk data location in the file
                    headers = {
                        "Content-Length": "{}".format(chunk_size),
                        "Content-Range": "bytes {}-{}/{}".format(
                            start_index, end_index - 1, total_file_size
                        ),
                    }
                    # Upload one chunk at a time
                    chunk_data_upload = requests.put(
                        upload_session["uploadUrl"], data=chunk_data, headers=headers
                    )
                    print(chunk_data_upload)
                    print(chunk_data_upload.json())
                    i = i + 1
                return chunk_data_upload.json()
