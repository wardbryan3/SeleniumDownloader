"""TTWN NBC newFiles API adapter."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests

from ..models import Artifact, FileContract, Outcome, SourceResult


class NBCDownloader:
    name = "nbc"

    def __init__(self, api_url: str | None, api_key: str | None, affiliate: str = "News-247") -> None:
        self.api_url, self.api_key, self.affiliate = api_url, api_key, affiliate

    @property
    def new_files_url(self) -> str:
        if self.api_url is None:
            return ""
        if self.api_url.rstrip("/").endswith("newFiles"):
            return self.api_url
        return f"{self.api_url.rstrip('/')}/{self.affiliate}/newFiles"

    @staticmethod
    def _manifest_urls(response: requests.Response) -> list[str]:
        """TTWN currently returns a text URL manifest; accept documented JSON too."""
        try:
            payload = response.json()
        except ValueError:
            return [line.strip() for line in response.text.splitlines() if line.strip().startswith(("http://", "https://"))]
        files = payload.get("newFiles", payload.get("files", [])) if isinstance(payload, dict) else payload
        if not isinstance(files, list):
            raise TypeError("invalid newFiles response")
        urls: list[str] = []
        for item in files:
            candidate = item.get("url") if isinstance(item, dict) else item
            if not isinstance(candidate, str):
                raise TypeError("provider URL missing")
            urls.append(candidate)
        return urls

    def fetch(self, staging: Path) -> SourceResult:
        if not self.api_url or not self.api_key:
            return SourceResult(self.name, Outcome.FAILED, message="NBC endpoint not configured")
        headers = {"X-API-Key": self.api_key, "User-Agent": "audio-downloader/1"}
        try:
            response = requests.get(self.new_files_url, headers=headers, timeout=30)
            response.raise_for_status()
            urls = self._manifest_urls(response)
            if not urls:
                return SourceResult(self.name, Outcome.IDLE)
            staging.mkdir(parents=True, exist_ok=True)
            artifacts: list[Artifact] = []
            for url in urls:
                filename = Path(urlparse(url).path).name
                if not filename:
                    raise ValueError("provider filename missing")
                target = staging / filename
                with requests.get(url, headers=headers, stream=True, timeout=90) as download:
                    download.raise_for_status()
                    with target.open("wb") as handle:
                        for chunk in download.iter_content(1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                artifacts.append(Artifact(target, FileContract(filename, destination="NBC")))
            return SourceResult(self.name, Outcome.SUCCESS, artifacts)
        except (OSError, TypeError, ValueError, requests.RequestException) as error:
            return SourceResult(self.name, Outcome.FAILED, message=str(error))
