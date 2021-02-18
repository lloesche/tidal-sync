import sys
import contextlib
from pathlib import Path
from tqdm import tqdm
import logging
import tidal_dl
import requests
from aigpy.stringHelper import isNull
from argparse import ArgumentParser
from pprint import pprint

logging.getLogger("tidal-sync").setLevel(logging.INFO)
logging.basicConfig(
    level=logging.WARN,
    format="%(asctime)s - %(levelname)s - %(process)d/%(threadName)s - %(message)s",
)
log = logging.getLogger("tidal-sync")

argv = sys.argv[1:]
if "-v" in argv or "--verbose" in argv:
    logging.getLogger("tidal-sync").setLevel(logging.DEBUG)


def main() -> None:
    arg_parser = get_arg_parser()
    arg_parser.parse_args()
    log.info("TIDAL-Sync starting up")
    tidal_dl.checkLogin()
    uri = f"https://listen.tidal.com/v1/users/{tidal_dl.TOKEN.userid}/favorites/ids"
    header = {
        "authorization": "Bearer {}".format(tidal_dl.TOKEN.accessToken),
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
    }
    params = {"countryCode": tidal_dl.TOKEN.countryCode}
    respond = requests.get(uri, headers=header, params=params)
    favorites = respond.json()
    album_dir = Path(tidal_dl.CONF.downloadPath + "/Album")
    artist_dirs = [d for d in album_dir.iterdir() if d.is_dir()]
    local_albums = []
    downloads = []
    for artist_dir in artist_dirs:
        album_dirs = [d.name for d in artist_dir.iterdir() if d.is_dir()]
        local_albums.extend(album_dirs)
    for album in favorites.get("ALBUM", []):
        album_str = f"[{album}]"
        if not any([s for s in local_albums if album_str in s]):
            log.info(f"Downloading {album}")
            downloads.append(album)
    for album in tqdm(downloads):
        with nostdout():
            tidal_dl.start(tidal_dl.TOKEN, tidal_dl.CONF, album)


def get_arg_parser() -> ArgumentParser:
    arg_parser = ArgumentParser(description="TIDAL-Sync")
    arg_parser.add_argument(
        "--verbose",
        "-v",
        help="Verbose logging",
        dest="verbose",
        action="store_true",
        default=False,
    )
    return arg_parser


class DummyFile(object):
  file = None
  def __init__(self, file):
    self.file = file

  def write(self, x):
    # Avoid print() second call (useless \n)
    if len(x.rstrip()) > 0:
        tqdm.write(x, file=self.file)


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile(sys.stdout)
    yield
    sys.stdout = save_stdout


if __name__ == "__main__":
    main()
