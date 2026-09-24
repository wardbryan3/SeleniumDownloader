"""Staging-only direct HTTP and FTP source adapters."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlparse, urlunparse
from zoneinfo import ZoneInfo

import requests

from ..audio import AudioProcessingError, overlay_tag
from ..models import Artifact, FileContract, Outcome, SourceResult


class SourceDownloader(ABC):
    name: str

    @abstractmethod
    def fetch(self, staging: Path) -> SourceResult:
        """Fetch artifacts into private staging. Never publish here."""


class HttpDownloader(SourceDownloader):
    def __init__(self, name: str, url: str | None, contracts: list[FileContract], timeout: int = 90) -> None:
        self.name, self.url, self.contracts, self.timeout = name, url, contracts, timeout

    def _download(self, staging: Path, filename: str) -> Path:
        if not self.url:
            raise ValueError("endpoint not configured")
        parsed = urlparse(self.url)
        if parsed.hostname and parsed.hostname.endswith("dropbox.com"):
            query = dict(parse_qsl(parsed.query))
            query["dl"] = "1"
            download_url = urlunparse(parsed._replace(query=urlencode(query)))
        else:
            download_url = self.url
        path = staging / filename
        with requests.get(download_url, stream=True, timeout=self.timeout) as response:
            response.raise_for_status()
            with path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        return path

    def fetch(self, staging: Path) -> SourceResult:
        staging.mkdir(parents=True, exist_ok=True)
        try:
            artifacts = [Artifact(self._download(staging, item.filename), item) for item in self.contracts]
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, requests.RequestException, ValueError) as error:
            return SourceResult(self.name, Outcome.FAILED, message=str(error))


class ZipDownloader(HttpDownloader):
    def fetch(self, staging: Path) -> SourceResult:
        staging.mkdir(parents=True, exist_ok=True)
        try:
            archive = self._download(staging, "source.zip")
            artifacts: list[Artifact] = []
            with zipfile.ZipFile(archive) as zip_handle:
                names = {Path(name).name: name for name in zip_handle.namelist()}
                for contract in self.contracts:
                    member = names.get(contract.filename)
                    if member is None:
                        raise ValueError(f"missing expected output {contract.filename}")
                    extracted = staging / contract.filename
                    with zip_handle.open(member) as source, extracted.open("wb") as target:
                        shutil.copyfileobj(source, target)
                    artifacts.append(Artifact(extracted, contract))
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, zipfile.BadZipFile, requests.RequestException, ValueError) as error:
            return SourceResult(self.name, Outcome.FAILED, message=str(error))


class NorthwestOutdoorsDownloader(ZipDownloader):
    """Select five stable carts and promo; ignore weekly dated full-program member."""

    SEGMENT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^nwoutdoors([1-5])\.mp3$", re.IGNORECASE)
    CARTS: ClassVar[tuple[str, ...]] = tuple(f"NWoutdoors{number}.mp3" for number in range(1, 6))
    PROMO_NAME = "NWoutdoors_promo.mp3"

    def __init__(self, url: str | None, tag_file: Path | None = None,
                 ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe") -> None:
        contracts = [FileContract(name) for name in self.CARTS]
        contracts.append(FileContract(self.PROMO_NAME, destination="Promos"))
        super().__init__("northwest_outdoors", url, contracts)
        self.tag_file, self.ffmpeg, self.ffprobe = tag_file, ffmpeg, ffprobe

    @classmethod
    def select_members(cls, names: list[str]) -> dict[str, str]:
        """Map verified stable members and reject ambiguous or incomplete archives."""
        selected: dict[str, str] = {}
        for member in names:
            filename = Path(member).name
            segment = cls.SEGMENT_PATTERN.fullmatch(filename)
            target = f"NWoutdoors{segment.group(1)}.mp3" if segment else (
                cls.PROMO_NAME if filename.lower() == cls.PROMO_NAME.lower() else None
            )
            if target is None:
                continue
            if target in selected:
                raise ValueError(f"duplicate Northwest member {target}")
            selected[target] = member
        if set(selected) != {*cls.CARTS, cls.PROMO_NAME}:
            raise ValueError("missing Northwest segments or promo")
        return selected

    def fetch(self, staging: Path) -> SourceResult:
        staging.mkdir(parents=True, exist_ok=True)
        try:
            archive = self._download(staging, "source.zip")
            with zipfile.ZipFile(archive) as zip_handle:
                members = self.select_members(zip_handle.namelist())
                artifacts = []
                for contract in self.contracts:
                    target = staging / contract.filename
                    with zip_handle.open(members[contract.filename]) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    artifacts.append(Artifact(target, contract))
            promo = next(item for item in artifacts if item.contract.destination == "Promos")
            if self.tag_file is None:
                raise AudioProcessingError("tag asset missing")
            tagged = promo.path.with_name(f"tagged-{promo.path.name}")
            overlay_tag(promo.path, self.tag_file, tagged, self.ffmpeg, self.ffprobe)
            promo.path.unlink()
            tagged.replace(promo.path)
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, zipfile.BadZipFile, requests.RequestException, ValueError, AudioProcessingError) as error:
            return SourceResult(self.name, Outcome.FAILED, message=str(error))


class WhittlerDownloader(ZipDownloader):
    PARTS: ClassVar[Mapping[str, str]] = MappingProxyType({
        "a": "Whittler1.mp3", "b": "Whittler2.mp3", "c": "Whittler3.mp3", "d": "Whittler4.mp3",
    })

    def __init__(self, url: str | None) -> None:
        super().__init__("whittler", url, [FileContract(filename) for filename in self.PARTS.values()])

    def fetch(self, staging: Path) -> SourceResult:
        staging.mkdir(parents=True, exist_ok=True)
        try:
            archive = self._download(staging, "source.zip")
            found: dict[str, str] = {}
            with zipfile.ZipFile(archive) as zip_handle:
                for member in zip_handle.namelist():
                    name = Path(member).name
                    matched = re.search(r"(?:part|pt)[ _.-]*([a-d])(?:\b|[_.-])", name, re.IGNORECASE)
                    if matched and name.lower().endswith(".mp3"):
                        part = matched.group(1).lower()
                        if part in found:
                            raise ValueError(f"duplicate Whittler part {part.upper()}")
                        found[part] = member
                if set(found) != set(self.PARTS):
                    raise ValueError("missing Whittler Parts A-D")
                artifacts = []
                for part, filename in self.PARTS.items():
                    target = staging / filename
                    with zip_handle.open(found[part]) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    artifacts.append(Artifact(target, FileContract(filename)))
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, zipfile.BadZipFile, requests.RequestException, ValueError) as error:
            return SourceResult(self.name, Outcome.FAILED, message=str(error))


class FtpDownloader(SourceDownloader):
    def __init__(self, name: str, host: str | None, username: str | None, password: str | None,
                 contracts: list[FileContract]) -> None:
        self.name, self.host, self.username, self.password, self.contracts = name, host, username, password, contracts

    @contextmanager
    def secure_curl(self) -> Iterator[tuple[list[str], str]]:
        """Yield explicit-FTPS curl arguments without exposing credentials in argv."""
        host, username, password = self.host, self.username, self.password
        if host is None or username is None or password is None:
            raise ValueError("FTP contract not configured")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as credentials:
            credentials.write(f'user = "{username}:{password}"\n')
            credentials_path = credentials.name
        try:
            yield (["curl", "--fail", "--silent", "--show-error", "--ssl-reqd", "--config", credentials_path], host)
        finally:
            Path(credentials_path).unlink(missing_ok=True)

    @contextmanager
    def insecure_curl(self) -> Iterator[tuple[list[str], str]]:
        """Yield plain-FTP arguments only for explicitly authorized providers."""
        host, username, password = self.host, self.username, self.password
        if host is None or username is None or password is None:
            raise ValueError("FTP contract not configured")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as credentials:
            credentials.write(f'user = "{username}:{password}"\n')
            credentials_path = credentials.name
        try:
            yield (["curl", "--fail", "--silent", "--show-error", "--config", credentials_path], host)
        finally:
            Path(credentials_path).unlink(missing_ok=True)

    @staticmethod
    def _ftp_url(host: str, remote_path: str = "") -> str:
        # ftp:// plus --ssl-reqd uses explicit FTPS, normally port 21.
        return f"ftp://{host}/{quote(remote_path)}"

    def list_files(self, common: list[str], host: str, remote_path: str = "") -> list[str]:
        directory = f"{remote_path.rstrip('/')}/" if remote_path else ""
        listing = subprocess.run([*common, "--list-only", self._ftp_url(host, directory)], check=True,
                                 capture_output=True, text=True, timeout=300)
        return [name for name in listing.stdout.splitlines() if name not in {".", ".."}]

    def download_file(self, common: list[str], host: str, remote_path: str, target: Path) -> None:
        subprocess.run([*common, "--output", str(target), self._ftp_url(host, remote_path)],
                       check=True, capture_output=True, text=True, timeout=300)

    def fetch(self, staging: Path) -> SourceResult:
        staging.mkdir(parents=True, exist_ok=True)
        try:
            with self.secure_curl() as (common, host):
                names = set(self.list_files(common, host))
                artifacts = []
                for contract in self.contracts:
                    if contract.filename not in names:
                        raise ValueError(f"missing expected output {contract.filename}")
                    target = staging / contract.filename
                    self.download_file(common, host, contract.filename, target)
                    artifacts.append(Artifact(target, contract))
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            outcome = Outcome.UNVERIFIED if str(error) == "FTP contract not configured" else Outcome.FAILED
            return SourceResult(self.name, outcome, message=str(error))


class MelindaMyersDownloader(FtpDownloader):
    """Fetch five weekly carts from provider's verified 5x-per-week FTPS directory."""

    CARTS: ClassVar[tuple[str, ...]] = ("MMMON.mp3", "MMTUE.mp3", "MMWED.mp3", "MMTHU.mp3", "MMFRI.mp3")
    DATE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^(\d{2})(\d{2})(\d{2})_")

    def __init__(self, host: str | None, username: str | None, password: str | None) -> None:
        super().__init__("melinda_myers", host, username, password, [FileContract(name) for name in self.CARTS])

    @classmethod
    def map_coming_week(cls, filenames: list[str], today: date) -> dict[str, str]:
        """Map verified `MMDDYY_` provider filenames to Monday-Friday carts."""
        mapped: dict[str, str] = {}
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        coming_monday = today + timedelta(days=days_until_monday)
        expected = {coming_monday + timedelta(days=index): cls.CARTS[index] for index in range(5)}
        for filename in filenames:
            matched = cls.DATE_PATTERN.match(Path(filename).name)
            if matched is None:
                continue
            try:
                published = date(2000 + int(matched.group(3)), int(matched.group(1)), int(matched.group(2)))
            except ValueError:
                continue
            cart = expected.get(published)
            if cart is not None:
                if cart in mapped:
                    raise ValueError(f"duplicate Melinda file for {cart}")
                mapped[cart] = filename
        if set(mapped) != set(cls.CARTS):
            raise ValueError("missing coming-week Melinda carts")
        return mapped

    def fetch(self, staging: Path) -> SourceResult:
        staging.mkdir(parents=True, exist_ok=True)
        try:
            with self.secure_curl() as (common, host):
                directories = self.list_files(common, host)
                required = ("audio_tips_3x_per_week", "audio_tips_5x_per_week")
                matching = {label: [name for name in directories if label in name.lower()] for label in required}
                if any(len(found) != 1 for found in matching.values()):
                    raise ValueError("expected one Melinda 3x and one 5x directory")
                remote_files = [f"{found[0]}/{name}" for found in matching.values()
                                for name in self.list_files(common, host, found[0])]
                mapping = self.map_coming_week(remote_files, datetime.now(ZoneInfo("America/Los_Angeles")).date())
                artifacts = []
                for cart in self.CARTS:
                    remote_name = mapping[cart]
                    target = staging / cart
                    self.download_file(common, host, remote_name, target)
                    artifacts.append(Artifact(target, FileContract(cart), remote_date=Path(remote_name).name[:6]))
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            outcome = Outcome.UNVERIFIED if str(error) == "FTP contract not configured" else Outcome.FAILED
            return SourceResult(self.name, outcome, message=str(error))


class WeekendInTheCountryDownloader(FtpDownloader):
    ROOT_DIRECTORY = "Weekend in the Country"

    def __init__(self, host: str | None, username: str | None, password: str | None, contracts: list[FileContract]) -> None:
        super().__init__("weekend_in_the_country", host, username, password, contracts)

    @staticmethod
    def select_upcoming_saturday_promo(filenames: list[str], today: date) -> str | None:
        """Pick nearest future dated promo; leave later promo untouched."""
        candidates: list[tuple[date, str]] = []
        for filename in filenames:
            matched = re.search(r"(?:(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)|([01]\d)-([0-3]\d)-(\d{2}))", filename)
            if not matched or "promo" not in filename.lower():
                continue
            groups = matched.groups()
            try:
                candidate = (date(int(groups[0]), int(groups[1]), int(groups[2])) if groups[0]
                             else date(2000 + int(groups[5]), int(groups[3]), int(groups[4])))
            except ValueError:
                continue
            if candidate >= today and candidate.weekday() == 5:
                candidates.append((candidate, filename))
        return min(candidates, default=(date.max, ""))[1] or None

    def fetch(self, staging: Path) -> SourceResult:
        """Use authorized plain FTP once per scheduled run; never silently downgrade FTPS."""
        staging.mkdir(parents=True, exist_ok=True)
        try:
            with self.insecure_curl() as (common, host):
                roots = self.list_files(common, host)
                if self.ROOT_DIRECTORY not in roots:
                    raise ValueError("WITC root directory missing")
                remote_names = self.list_files(common, host, self.ROOT_DIRECTORY)
                segments = sorted(name for name in remote_names if re.search(r"hr\d+_seg\d+.*\.mp3$", name, re.IGNORECASE))
                promo = self.select_upcoming_saturday_promo(remote_names, datetime.now(ZoneInfo("America/Los_Angeles")).date())
                if len(segments) != 8 or promo is None:
                    raise ValueError("expected eight WITC segments and one upcoming-Saturday promo")
                files = [*segments, promo]
                artifacts = []
                for filename in files:
                    target = staging / filename
                    self.download_file(common, host, f"{self.ROOT_DIRECTORY}/{filename}", target)
                    contract = next((item for item in self.contracts if item.filename == filename), FileContract(filename))
                    artifacts.append(Artifact(target, contract))
            return SourceResult(self.name, Outcome.SUCCESS, artifacts,
                                message="authorized insecure plain-FTP transport", details={"insecure_transport": True})
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            outcome = Outcome.UNVERIFIED if str(error) == "FTP contract not configured" else Outcome.FAILED
            return SourceResult(self.name, outcome, message=str(error))


class _CowPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[tuple[str, list[dict[str, str]]]] = []
        self._action = ""
        self._inputs: list[dict[str, str]] | None = None
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value or "" for name, value in attrs}
        if tag == "form":
            self._action, self._inputs = values.get("action", ""), []
        elif tag == "input" and self._inputs is not None:
            self._inputs.append(values)
        elif tag == "a" and values.get("href", "").lower().split("?", 1)[0].endswith(".mp3"):
            self.links.append(values["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._inputs is not None:
            self.forms.append((self._action, self._inputs))
            self._inputs = None


class ClearOutWestDownloader(SourceDownloader):
    """Verified HTTPS form session; no browser fallback or credential leakage."""
    name = "clear_out_west"

    def __init__(self, url: str | None, password: str | None, contracts: list[FileContract]) -> None:
        self.url, self.password, self.contracts = url, password, contracts

    def fetch(self, staging: Path) -> SourceResult:
        if not self.url or not self.password:
            return SourceResult(self.name, Outcome.UNVERIFIED, message="COW session credentials missing")
        try:
            session = requests.Session()
            session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"
            page = session.get(self.url, timeout=30)
            page.raise_for_status()
            parser = _CowPageParser()
            parser.feed(page.text)
            form = next(((action, inputs) for action, inputs in parser.forms if any(item.get("name") == "p" for item in inputs)), None)
            if form is None:
                raise ValueError("COW login form missing")
            action, inputs = form
            data = {item["name"]: item.get("value", "") for item in inputs if item.get("name")}
            data["p"] = self.password
            authenticated = session.post(urljoin(page.url, action or page.url), data=data, timeout=30)
            authenticated.raise_for_status()
            parser = _CowPageParser()
            parser.feed(authenticated.text)
            links: dict[str, str] = {}
            for link in parser.links:
                filename = Path(urlparse(urljoin(authenticated.url, link)).path).name
                matched = re.search(r"track0*(\d+)\.mp3$", filename, re.IGNORECASE)
                if matched is None:
                    continue
                number = int(matched.group(1))
                target_name = "COWPROMO.mp3" if number == 5 else f"COW{number}.mp3"
                if target_name in links:
                    raise ValueError(f"duplicate COW track {number}")
                links[target_name] = urljoin(authenticated.url, link)
            expected = {item.filename for item in self.contracts}
            if expected != {"COW1.mp3", "COW2.mp3", "COW3.mp3", "COW4.mp3", "COWPROMO.mp3"} or set(links) != expected:
                raise ValueError("COW response must contain exactly five contracted tracks")
            staging.mkdir(parents=True, exist_ok=True)
            artifacts = []
            for contract in self.contracts:
                target = staging / contract.filename
                with session.get(links[contract.filename], stream=True, timeout=90) as response:
                    response.raise_for_status()
                    with target.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                artifacts.append(Artifact(target, contract))
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, ValueError, requests.RequestException) as error:
            return SourceResult(self.name, Outcome.FAILED, message=str(error))


class AgInfoDownloader(SourceDownloader):
    """Stream three provider feeds; Content-Length is deliberately optional."""

    CARTS: ClassVar[tuple[str, ...]] = ("AGRIBIZ.mp3", "MARKETAG.mp3", "LOA.mp3")

    def __init__(self, urls: tuple[str, ...]) -> None:
        self.name, self.urls = "aginfo", urls

    def fetch(self, staging: Path) -> SourceResult:
        if len(self.urls) != len(self.CARTS):
            return SourceResult(self.name, Outcome.UNVERIFIED, message="AgInfo requires three endpoint URLs")
        staging.mkdir(parents=True, exist_ok=True)
        try:
            artifacts: list[Artifact] = []
            for url, filename in zip(self.urls, self.CARTS, strict=True):
                target = staging / filename
                with requests.get(url, stream=True, timeout=90) as response:
                    response.raise_for_status()
                    with target.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                artifacts.append(Artifact(target, FileContract(filename)))
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, requests.RequestException) as error:
            return SourceResult(self.name, Outcome.FAILED, message=str(error))


class RodeoShowDownloader(HttpDownloader):
    def __init__(self, url: str | None = None, contract: FileContract | None = None) -> None:
        super().__init__("rodeoshow", url, [contract or FileContract("RODEOSHOW.mp3", minimum_bytes=1_000_000)])
