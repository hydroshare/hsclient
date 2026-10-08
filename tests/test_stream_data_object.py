from unittest.mock import MagicMock, patch

import pytest

from hsclient.hydroshare import HydroShare


@pytest.fixture
def hs_with_s3():
    """A HydroShare client with a mocked s3fs S3FileSystem attached (no network)."""
    hs = HydroShare()  # no username/password -> no network calls, s3_client is None
    mock_s3_client = MagicMock()
    hs._s3_client = mock_s3_client
    return hs, mock_s3_client


S3_BASE = "test-bucket/abc123/data/contents"


def test_stream_raises_without_s3_client():
    hs = HydroShare()
    assert hs.s3_client is None
    with pytest.raises(Exception, match="S3 client is not available"):
        hs.stream_data_object(f"{S3_BASE}/my_data.zarr")


def test_stream_unsupported_extension_raises(hs_with_s3):
    hs, _ = hs_with_s3
    with pytest.raises(ValueError, match="Unsupported file format '.txt'"):
        hs.stream_data_object(f"{S3_BASE}/notes.txt")


def test_stream_invalid_object_type_pair_raises(hs_with_s3):
    """A parquet file cannot be loaded as an xarray object (core acceptance check)."""
    hs, _ = hs_with_s3
    with pytest.raises(ValueError, match="Cannot load a '.parquet' file as 'xarray'"):
        hs.stream_data_object(f"{S3_BASE}/table.parquet", object_type="xarray")


def test_stream_deferred_format_raises_not_implemented(hs_with_s3):
    """Multi-file / non-seekable formats are registered but not yet streamable."""
    hs, _ = hs_with_s3
    for path in (f"{S3_BASE}/layer.shp", f"{S3_BASE}/raster.vrt", f"{S3_BASE}/series.sqlite"):
        with pytest.raises(NotImplementedError, match="is not supported yet"):
            hs.stream_data_object(path)


def test_stream_deferred_format_validates_object_type_first(hs_with_s3):
    """An invalid object_type on a deferred format still fails validation before the guard."""
    hs, _ = hs_with_s3
    with pytest.raises(ValueError, match="Cannot load a '.sqlite' file as 'xarray'"):
        hs.stream_data_object(f"{S3_BASE}/series.sqlite", object_type="xarray")


def test_stream_zarr_dispatches_to_open_zarr(hs_with_s3):
    hs, mock_s3_client = hs_with_s3
    store = object()
    mock_s3_client.get_mapper.return_value = store
    with patch("hsclient.hydroshare.xarray") as mock_xarray:
        result = hs.stream_data_object(f"{S3_BASE}/my_data.zarr")

    mock_s3_client.get_mapper.assert_called_once_with(f"{S3_BASE}/my_data.zarr")
    mock_xarray.open_zarr.assert_called_once_with(store)
    assert result is mock_xarray.open_zarr.return_value


def test_stream_csv_dispatches_to_read_csv(hs_with_s3):
    hs, mock_s3_client = hs_with_s3
    with patch("hsclient.hydroshare.pandas") as mock_pandas:
        result = hs.stream_data_object(f"{S3_BASE}/data.csv")

    mock_s3_client.open.assert_called_once_with(f"{S3_BASE}/data.csv")
    assert mock_pandas.read_csv.call_count == 1
    assert result is mock_pandas.read_csv.return_value


def test_stream_parquet_defaults_to_pandas(hs_with_s3):
    hs, mock_s3_client = hs_with_s3
    with patch("hsclient.hydroshare.pandas") as mock_pandas:
        result = hs.stream_data_object(f"{S3_BASE}/table.parquet")

    assert mock_pandas.read_parquet.call_count == 1
    assert result is mock_pandas.read_parquet.return_value


def test_stream_parquet_as_pyarrow(hs_with_s3):
    hs, mock_s3_client = hs_with_s3
    with patch("hsclient.hydroshare.pyarrow_parquet") as mock_pq:
        result = hs.stream_data_object(f"{S3_BASE}/table.parquet", object_type="pyarrow")

    assert mock_pq.read_table.call_count == 1
    assert result is mock_pq.read_table.return_value


def test_stream_netcdf_uses_h5netcdf_engine(hs_with_s3):
    hs, mock_s3_client = hs_with_s3
    with patch("hsclient.hydroshare.xarray") as mock_xarray:
        hs.stream_data_object(f"{S3_BASE}/data.nc")

    _, kwargs = mock_xarray.open_dataset.call_args
    assert kwargs.get("engine") == "h5netcdf"


def test_stream_tif_dispatches_to_rasterio(hs_with_s3):
    hs, mock_s3_client = hs_with_s3
    with patch("hsclient.hydroshare.rasterio") as mock_rasterio:
        result = hs.stream_data_object(f"{S3_BASE}/dem.tif")

    assert mock_rasterio.open.call_count == 1
    assert result is mock_rasterio.open.return_value


def test_stream_missing_dependency_raises(hs_with_s3):
    hs, _ = hs_with_s3
    with patch("hsclient.hydroshare.xarray", None):
        with pytest.raises(Exception, match="xarray package was not found"):
            hs.stream_data_object(f"{S3_BASE}/my_data.zarr")


@pytest.mark.integration
def test_stream_zarr_to_xarray_integration(hydroshare, new_resource):
    """
    End-to-end: write a small zarr store to a resource's S3 location, then stream it back into
    an xarray.Dataset without downloading. Requires a HydroShare/S3 backend and xarray+zarr.
    """
    xarray = pytest.importorskip("xarray")
    pytest.importorskip("zarr")
    import numpy as np

    assert hydroshare.s3_client is not None, "S3 client required for this integration test"

    ds = xarray.Dataset(
        {"temperature": ("time", np.arange(5, dtype="float64"))},
        coords={"time": np.arange(5)},
    )
    zarr_s3_path = f"{new_resource.s3_path}/sample.zarr"
    ds.to_zarr(hydroshare.s3_client.get_mapper(zarr_s3_path), mode="w")

    streamed = hydroshare.stream_data_object(zarr_s3_path)
    assert streamed.__class__.__name__ == "Dataset"
    assert int(streamed.sizes["time"]) == 5
