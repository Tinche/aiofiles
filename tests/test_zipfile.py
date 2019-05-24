import zipfile
from os.path import dirname, join
from aiofiles import zipfile as aio_zipfile
import pytest


def test_all_exports_exist():
    Missing = object()
    for export in zipfile.__all__:
        assert export in aio_zipfile.__all__
        assert getattr(aio_zipfile, export, Missing) is not Missing


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('SyncFile', 'AsyncFile'), (
        (zipfile.ZipFile, aio_zipfile.ZipFile),
        (zipfile.PyZipFile, aio_zipfile.PyZipFile),
    )
)
async def test_zipfile_opens(SyncFile, AsyncFile):
    filename = join(dirname(__file__), 'resources', 'zipfile.zip')

    with SyncFile(filename) as expected_file:
        expected_namelist = expected_file.namelist()
        expected_file_filename = expected_namelist[0]
        expected_file_unzipped = expected_file.read(expected_file_filename)

    async with AsyncFile(filename) as actual_file:
        actual_namelist = actual_file.namelist()
        assert len(expected_namelist) == len(actual_namelist)
        for name in expected_namelist:
            assert name in actual_namelist

        actual_file_unzipped = await actual_file.read(expected_file_filename)
        assert expected_file_unzipped == actual_file_unzipped

        # make sure open() works the same as read()
        async with actual_file.open(expected_file_filename) as actual_inner_file:
            open_unzipped = await actual_inner_file.read()
            assert actual_file_unzipped == open_unzipped


@pytest.mark.asyncio
@pytest.mark.parametrize('resource_fpath', ('zipfile.zip', 'test_file1.txt'))
async def test_is_zipfile(resource_fpath):
    is_zip_filename = join(dirname(__file__), 'resources', resource_fpath)
    expected = zipfile.is_zipfile(is_zip_filename)
    actual = await aio_zipfile.is_zipfile(is_zip_filename)
    assert expected == actual
