"""Unit tests for URL resolvers."""

import pytest
from src.gofile_transfer.resolvers.gdrive import GoogleDriveResolver
from src.gofile_transfer.resolvers.sourceforge import SourceForgeResolver
from src.gofile_transfer.resolvers.direct import DirectURLResolver
from src.gofile_transfer.resolvers.factory import ResolverFactory


def test_gdrive_file_id_extraction():
    resolver = GoogleDriveResolver()

    url1 = "https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I/view?usp=sharing"
    assert resolver.extract_file_id(url1) == "1A2B3C4D5E6F7G8H9I"

    url2 = "https://drive.google.com/uc?id=9I8H7G6F5E4D3C2B1A&export=download"
    assert resolver.extract_file_id(url2) == "9I8H7G6F5E4D3C2B1A"

    url3 = "https://docs.google.com/d/XYZ_12345/edit"
    assert resolver.extract_file_id(url3) == "XYZ_12345"


def test_gdrive_can_handle():
    resolver = GoogleDriveResolver()
    assert resolver.can_handle("https://drive.google.com/file/d/abc/view") is True
    assert resolver.can_handle("https://github.com/test/repo") is False


def test_sourceforge_can_handle():
    resolver = SourceForgeResolver()
    assert resolver.can_handle("https://sourceforge.net/projects/7-zip/files/7-Zip/23.01/7z2301-x64.exe/download") is True
    assert resolver.can_handle("https://google.com") is False


def test_direct_dropbox_conversion():
    resolver = DirectURLResolver()
    url = "https://www.dropbox.com/s/abcdef12345/example.zip?dl=0"
    converted = resolver._convert_known_share_links(url)
    assert "dl=1" in converted


def test_factory_matching():
    factory = ResolverFactory()
    gdrive_res = factory.resolve  # checking method exists
    assert callable(gdrive_res)
