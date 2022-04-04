import optparse
import os
from ast import arg

from simple_onedrive_client.client import SimpleOneDriveClient


def parse_args():

    parser = optparse.OptionParser()

    parser.add_option(
        "--src-file-path",
        action="store",
        dest="source_file_path",
        help="Source file path",
    )

    parser.add_option(
        "--dst-path",
        action="store",
        dest="dst_path",
        help="destination path on onedrive",
    )
    parser.add_option(
        "--dst-fn",
        action="store",
        dest="dst_fn",
        help="destination filename on onedrive",
    )
    parser.add_option(
        "--client-id",
        action="store",
        dest="client_id",
        help="Onedrive Client Id",
    )

    parser.add_option(
        "--client-secret",
        action="store",
        dest="client_secret",
        help="Onedrive Client Secret",
    )
    parser.add_option(
        "--token-fn",
        action="store",
        dest="token_fn",
        help="Token File name",
    )
    options, _ = parser.parse_args()
    source_file_path = options.source_file_path
    dst_path = options.dst_path
    dst_fn = options.dst_fn
    client_id = options.client_id
    client_secret = options.client_secret
    token_fn = options.token_fn

    return {
        "source_file_path": source_file_path,
        "dst_path": dst_path,
        "dst_fn": dst_fn,
        "client_id": client_id,
        "client_secret": client_secret,
        "token_fn": token_fn,
    }


if __name__ == "__main__":
    args = parse_args()
    print(args)

    def dump_token_to_file(new_token: str):
        with open(args["token_fn"], "w") as f:
            f.write(new_token)

    client = SimpleOneDriveClient(
        client_id=args["client_id"],
        secret=args["client_secret"],
        token_updated=dump_token_to_file,
    )
    loaded_successfully = False
    if os.path.exists(args["token_fn"]):
        with open(args["token_fn"], "r") as f:
            loaded_successfully = client.load_auth(token_fn=args["token_fn"])
    if not loaded_successfully or client.auth is None:
        print(f"Please use the following url to login:{client.get_login_url()}")
        code = input("Please input the code:")
        client.complete_login_using_code(code)
    res = client.upload_file(
        file_name=args["dst_fn"],
        file_full_path=args["source_file_path"],
        one_drive_dest_path=args["dst_path"],
    )
    print(res)
