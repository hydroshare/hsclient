import os
import pathlib
import tempfile

import fiona
import pytest
import rasterio
from fiona.model import to_dict
from hsmodels.schemas.enums import AggregationType
from rasterio.windows import Window

from hsclient import (
    GeoFeatureAggregation,
    GeoRasterAggregation,
    NetCDFAggregation,
    TimeseriesAggregation,
    CSVAggregation,
)


@pytest.mark.parametrize("search_by", ["type", "file_path"])
def test_timeseries_as_data_object(timeseries_resource, search_by):
    timeseries_resource.refresh()
    if search_by == 'type':
        aggr = timeseries_resource.aggregation(type=AggregationType.TimeSeriesAggregation)
    else:
        file_path = "ODM2_Multi_Site_One_Variable.sqlite"
        aggr = timeseries_resource.aggregation(file__path=file_path)

    assert type(aggr) is TimeseriesAggregation
    series_result = next(
        r for r in aggr.metadata.time_series_results if r.series_id == "2837b7d9-1ebc-11e6-a16e-f45c8999816f"
    )

    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = timeseries_resource.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        # load timseries data for the specified series to pandas DataFrame
        pd_dataframe = aggr.as_data_object(agg_path=agg_path, series_id=series_result.series_id)
        assert len(pd_dataframe) == 1333


@pytest.mark.parametrize("as_new_aggr", [False, True])
def test_timeseries_save_data_object(timeseries_resource, as_new_aggr):
    timeseries_resource.refresh()
    file_path = "ODM2_Multi_Site_One_Variable.sqlite"
    aggr = timeseries_resource.aggregation(file__path=file_path)
    assert aggr is not None
    assert type(aggr) is TimeseriesAggregation
    series_id = '4a6f095c-1ebc-11e6-8a10-f45c8999816f'
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = timeseries_resource.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        pd_dataframe = aggr.as_data_object(agg_path=agg_path, series_id=series_id)
        assert pd_dataframe.__class__.__name__ == "DataFrame"
        rows, columns = pd_dataframe.shape
        # delete 10 rows
        pd_dataframe.drop(pd_dataframe.index[0:10], axis=0, inplace=True)
        dst_path = ""
        if as_new_aggr:
            dst_path = "raster_aggr_folder"
            timeseries_resource.folder_create(dst_path)

        aggr = aggr.save_data_object(resource=timeseries_resource, agg_path=agg_path, as_new_aggr=as_new_aggr,
                                     destination_path=dst_path)
        assert type(aggr) is TimeseriesAggregation

    # check the updated/new timeseries aggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        if as_new_aggr:
            file_path = f"{dst_path}/{file_path}"

        aggr = timeseries_resource.aggregation(file__path=file_path)
        assert aggr is not None
        assert type(aggr) is TimeseriesAggregation

        agg_path = timeseries_resource.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        pd_dataframe = aggr.as_data_object(agg_path=agg_path, series_id=series_id)
        updated_rows, update_columns = pd_dataframe.shape
        assert rows == updated_rows + 10
        assert columns == update_columns


@pytest.mark.parametrize("search_by", ["type", "file_path"])
def test_raster_as_data_object(resource_with_raster_aggr, search_by):
    resource_with_raster_aggr.refresh()
    if search_by == "type":
        aggr = resource_with_raster_aggr.aggregation(type=AggregationType.GeographicRasterAggregation)
    else:
        file_path = "logan.vrt"
        aggr = resource_with_raster_aggr.aggregation(file__path=file_path)

    assert type(aggr) is GeoRasterAggregation

    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_raster_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)

        dataset = aggr.as_data_object(agg_path=agg_path)
        assert dataset.__class__.__name__ == "DatasetReader"
        # raster should have 1 band
        assert dataset.count == 1


@pytest.mark.parametrize("as_new_aggr", [False, True])
def test_raster_save_data_object(resource_with_raster_aggr, as_new_aggr):
    resource_with_raster_aggr.refresh()
    file_path = "logan.vrt"
    aggr = resource_with_raster_aggr.aggregation(file__path=file_path)
    assert aggr is not None
    assert type(aggr) is GeoRasterAggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_raster_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        rasterio_reader = aggr.as_data_object(agg_path=agg_path)
        assert rasterio_reader.__class__.__name__ == "DatasetReader"
        # edit raster data - sub-setting the dataset
        new_width = rasterio_reader.width - 9
        new_height = rasterio_reader.height - 10
        updated_width = new_width
        updated_height = new_height
        subset_window = Window(0, 0, new_width, new_height)
        subset_band = rasterio_reader.read(1, window=subset_window)
        output_raster_dir_path = os.path.join(tmp, "updated_aggr")
        os.makedirs(output_raster_dir_path)
        update_raster_filename = "updated_logan.tif"
        output_raster_file_path = os.path.join(output_raster_dir_path, update_raster_filename)
        profile = rasterio_reader.profile
        rasterio_reader.close()
        profile['driver'] = "GTiff"
        profile['width'] = new_width
        profile['height'] = new_height

        with rasterio.open(output_raster_file_path, "w", **profile) as dst:
            dst.write(subset_band, 1)

        dst_path = ""
        if as_new_aggr:
            dst_path = "raster_aggr_folder"
            resource_with_raster_aggr.folder_create(dst_path)

        # save the new tif file to update the aggregation or create a new aggregation
        aggr = aggr.save_data_object(resource=resource_with_raster_aggr, agg_path=output_raster_dir_path,
                                     as_new_aggr=as_new_aggr, destination_path=dst_path)
        assert aggr is not None
        assert type(aggr) is GeoRasterAggregation

    # check the updated raster aggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        file_path = pathlib.Path(update_raster_filename).stem + ".vrt"
        if as_new_aggr:
            file_path = f"{dst_path}/{file_path}"

        aggr = resource_with_raster_aggr.aggregation(file__path=file_path)
        assert aggr is not None
        assert type(aggr) is GeoRasterAggregation

        agg_path = resource_with_raster_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        rasterio_reader = aggr.as_data_object(agg_path=agg_path)
        assert updated_height == rasterio_reader.height
        assert updated_width == rasterio_reader.width


@pytest.mark.parametrize("search_by", ["type", "file_path"])
def test_netcdf_as_data_object(resource_with_netcdf_aggr, search_by):
    resource_with_netcdf_aggr.refresh()
    if search_by == 'type':
        aggr = resource_with_netcdf_aggr.aggregation(type=AggregationType.MultidimensionalAggregation)
    else:
        file_path = "SWE_time.nc"
        aggr = resource_with_netcdf_aggr.aggregation(file__path=file_path)

    assert type(aggr) is NetCDFAggregation

    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_netcdf_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        dataset = aggr.as_data_object(agg_path=agg_path)
        assert dataset.__class__.__name__ == "Dataset"
        # netcdf dimensions
        assert dataset.dims['time'] == 2184


@pytest.mark.parametrize("as_new_aggr", [False, True])
def test_netcdf_save_data_object(resource_with_netcdf_aggr, as_new_aggr):
    resource_with_netcdf_aggr.refresh()
    file_path = "SWE_time.nc"
    aggr = resource_with_netcdf_aggr.aggregation(file__path=file_path)
    assert aggr is not None
    assert type(aggr) is NetCDFAggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_netcdf_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        xr_dataset = aggr.as_data_object(agg_path=agg_path)
        assert xr_dataset.__class__.__name__ == "Dataset"
        agg_title = "This is a modified title for this aggregation by hsclient"
        xr_dataset.attrs["title"] = agg_title
        dst_path = ""
        if as_new_aggr:
            dst_path = "netcdf_aggr_folder"
            resource_with_netcdf_aggr.folder_create(dst_path)

        aggr = aggr.save_data_object(resource=resource_with_netcdf_aggr, agg_path=agg_path, as_new_aggr=as_new_aggr,
                                     destination_path=dst_path)

        assert type(aggr) is NetCDFAggregation
        xr_dataset = aggr.as_data_object(agg_path=agg_path)
        assert xr_dataset.attrs["title"] == agg_title

    # check the updated/new netcdf aggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        if as_new_aggr:
            file_path = f"{dst_path}/{file_path}"

        aggr = resource_with_netcdf_aggr.aggregation(file__path=file_path)
        assert aggr is not None
        assert type(aggr) is NetCDFAggregation

        agg_path = resource_with_netcdf_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        xr_dataset = aggr.as_data_object(agg_path=agg_path)
        assert xr_dataset.attrs["title"] == agg_title


@pytest.mark.parametrize("search_by", ["type", "file_path"])
def test_geofeature_as_data_object(resource_with_geofeature_aggr, search_by):
    resource_with_geofeature_aggr.refresh()
    if search_by == "type":
        aggr = resource_with_geofeature_aggr.aggregation(type=AggregationType.GeographicFeatureAggregation)
    else:
        file_path = "watersheds.shp"
        aggr = resource_with_geofeature_aggr.aggregation(file__path=file_path)

    assert aggr is not None
    assert type(aggr) is GeoFeatureAggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_geofeature_aggr.aggregation_download(aggregation=aggr, save_path=tmp,
                                                                      unzip_to=unzip_to)
        fn_collection = aggr.as_data_object(agg_path=agg_path)
        assert fn_collection.__class__.__name__ == "Collection"
        # check projection type
        assert str(fn_collection.crs) == "EPSG:26912"
        # close the fiona collection object so that the temp dir can be cleaned up.
        fn_collection.close()


@pytest.mark.parametrize("as_new_aggr", [False, True])
def test_geofeature_save_data_object(resource_with_geofeature_aggr, as_new_aggr):
    resource_with_geofeature_aggr.refresh()
    file_path = "watersheds.shp"
    aggr = resource_with_geofeature_aggr.aggregation(file__path=file_path)
    assert aggr is not None
    assert type(aggr) is GeoFeatureAggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_geofeature_aggr.aggregation_download(aggregation=aggr, save_path=tmp,
                                                                      unzip_to=unzip_to)
        fn_collection = aggr.as_data_object(agg_path=agg_path)
        assert fn_collection.__class__.__name__ == "Collection"
        original_shp_filename = os.path.basename(fn_collection.path)
        updated_shp_file_dir = os.path.join(tmp, "updated_aggr")
        os.makedirs(updated_shp_file_dir)
        output_shp_file_path = os.path.join(updated_shp_file_dir, original_shp_filename)
        with fiona.open(output_shp_file_path, 'w', schema=fn_collection.schema, driver=fn_collection.driver,
                        crs=fn_collection.crs) as out_shp_file:
            for feature in fn_collection:
                ft_dict = to_dict(feature)
                if ft_dict['properties']['Id'] < 5:
                    out_shp_file.write(feature)

        dst_path = ""
        if as_new_aggr:
            dst_path = "geo_aggr_folder"
            resource_with_geofeature_aggr.folder_create(dst_path)

        aggr = aggr.save_data_object(resource=resource_with_geofeature_aggr, agg_path=updated_shp_file_dir,
                                     as_new_aggr=as_new_aggr,  destination_path=dst_path)
        assert aggr is not None
        assert type(aggr) is GeoFeatureAggregation
        assert aggr.data_object is None

    # check the updated geo-feature aggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download aggregation
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        if as_new_aggr:
            file_path = f"{dst_path}/{file_path}"

        aggr = resource_with_geofeature_aggr.aggregation(file__path=file_path)
        assert aggr is not None
        assert type(aggr) is GeoFeatureAggregation

        agg_path = resource_with_geofeature_aggr.aggregation_download(aggregation=aggr, save_path=tmp,
                                                                      unzip_to=unzip_to)
        fn_collection = aggr.as_data_object(agg_path=agg_path)
        for feature in fn_collection:
            ft_dict = to_dict(feature)
            assert ft_dict['properties']['Id'] < 5
        # need to close the data object so that the tmp directory can be cleaned up
        fn_collection.close()


@pytest.mark.parametrize("search_by", ["type", "file_path"])
def test_csv_as_data_object(resource_with_csv_aggr, search_by):
    resource_with_csv_aggr.refresh()
    if search_by == "type":
        aggr = resource_with_csv_aggr.aggregation(type=AggregationType.CSVFileAggregation)
    else:
        file_path = "ecoregions.csv"
        aggr = resource_with_csv_aggr.aggregation(file__path=file_path)
    assert aggr is not None
    assert type(aggr) is CSVAggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_csv_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        # load csv data to data object as pandas dataframe
        pd_df = aggr.as_data_object(agg_path=agg_path)
        # test number of rows in pandas dataframe
        assert len(pd_df) == 2923
        # test number of columns
        assert len(pd_df.columns) == 4


@pytest.mark.parametrize("as_new_aggr", [False, True])
def test_csv_save_data_object(resource_with_csv_aggr, as_new_aggr):
    resource_with_csv_aggr.refresh()
    file_path = "ecoregions.csv"
    aggr = resource_with_csv_aggr.aggregation(file__path=file_path)
    assert aggr is not None
    assert type(aggr) is CSVAggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_csv_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        # load csv data to data object as pandas dataframe
        pd_df = aggr.as_data_object(agg_path=agg_path)
        # test number of rows in pandas dataframe
        assert len(pd_df) == 2923
        # test number of columns
        assert len(pd_df.columns) == 4
        # edit the dataframe - remove the last column in the dataframe
        pd_df.drop(pd_df.columns[-1], axis=1, inplace=True)
        assert len(pd_df.columns) == 3
        dst_path = ""
        if as_new_aggr:
            dst_path = "csv_aggr_folder"
            resource_with_csv_aggr.folder_create(dst_path)
        # save the dataframe to a new csv file
        aggr = aggr.save_data_object(resource=resource_with_csv_aggr, agg_path=agg_path, as_new_aggr=as_new_aggr,
                                     destination_path=dst_path)
        assert aggr is not None
        assert type(aggr) is CSVAggregation
        if as_new_aggr:
            assert aggr.data_object is None
        else:
            assert aggr.data_object is not None

    # check the updated csv aggregation
    with tempfile.TemporaryDirectory() as tmp:
        # download
        unzip_to = os.path.join(tmp, "unzipped_aggr")
        os.makedirs(unzip_to)
        agg_path = resource_with_csv_aggr.aggregation_download(aggregation=aggr, save_path=tmp, unzip_to=unzip_to)
        # load csv data to data object as pandas dataframe
        pd_df = aggr.as_data_object(agg_path=agg_path)
        # test number of rows in pandas dataframe
        assert len(pd_df) == 2923
        # test number of columns
        assert len(pd_df.columns) == 3
