import getpass
import os
import pathlib
import pickle
import shutil
import sqlite3
import tempfile
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime
from functools import wraps
from posixpath import basename, dirname, join as urljoin, splitext
from pprint import pformat
from typing import Callable, Dict, List, TYPE_CHECKING, Union
from urllib.parse import quote, unquote, urlparse
from uuid import uuid4
from zipfile import ZipFile

if TYPE_CHECKING:
    import fiona
    import pandas
    import rasterio
    import xarray
else:
    try:
        import fiona
    except ImportError:
        fiona = None
    try:
        import pandas
    except ImportError:
        pandas = None
    try:
        import rasterio
    except ImportError:
        rasterio = None
    try:
        import xarray
    except ImportError:
        xarray = None

import requests

from hsmodels.schemas import load_rdf, rdf_string
from hsmodels.schemas.base_models import BaseMetadata
from hsmodels.schemas.enums import AggregationType
from hsmodels.schemas.fields import BoxCoverage, PointCoverage
from requests_oauthlib import OAuth2Session

from hsclient.json_models import ResourcePreview, User
from hsclient.oauth2_model import Token
from hsclient.utils import attribute_filter, encode_resource_url, is_aggregation, main_file_type

CHECK_TASK_PING_INTERVAL = 10


class File(str):
    """
    A File path string representing the path to a file within a resource.
    :param value: the string path value
    :param file_url: the fully qualified url to the file on hydroshare.org
    :param checksum: the md5 checksum of the file
    """

    def __new__(cls, value, file_url, checksum):
        return super(File, cls).__new__(cls, value)

    def __init__(self, value, file_url, checksum):
        self._file_url = file_url
        self._checksum = checksum

    @property
    def path(self) -> str:
        """The path of the file"""
        return self

    @property
    def name(self) -> str:
        """The filename"""
        return basename(self)

    @property
    def extension(self) -> str:
        """The extension of the file"""
        return splitext(self.name)[1]

    @property
    def folder(self) -> str:
        """The folder the file is in"""
        return dirname(self)

    @property
    def checksum(self):
        """The md5 checksum of the file"""
        return self._checksum

    @property
    def url(self):
        """The url to the file on HydroShare"""
        return self._file_url


def refresh(f):
    """
    Decorator for refreshing metadata from HydroShare after the decorated method is called.
    The docstring of a decorated method is updated to include
    :param refresh: Defaults True, False to not refresh metadata from HydroShare
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        do_refresh = kwargs.pop("refresh", True)
        result = f(*args, **kwargs)
        if do_refresh:
            self.refresh()
        return result

    # update docstring to include refresh parameter
    doc_lines = f.__doc__.split("\n")
    insert_index = len(doc_lines) - 2
    doc_lines.insert(insert_index, ":param refresh: Defaults True, False to not refresh metadata from HydroShare")
    wrapper.__doc__ = "\n    ".join([l.strip() for l in doc_lines])

    return wrapper


class Aggregation:
    """Represents an Aggregation in HydroShare"""

    def __init__(self, map_path, hs_session, checksums=None):
        self._map_path = map_path
        self._hs_session = hs_session
        self._retrieved_map = None
        self._retrieved_metadata = None
        self._parsed_files = None
        self._parsed_aggregations = None
        self._parsed_checksums = checksums
        self._main_file_path = None

    def __str__(self):
        return self._map_path

    @property
    def _map(self):
        if not self._retrieved_map:
            self._retrieved_map = self._retrieve_and_parse(self._map_path)
        return self._retrieved_map

    @property
    def _metadata(self):
        if not self._retrieved_metadata:
            self._retrieved_metadata = self._retrieve_and_parse(self.metadata_path)
        return self._retrieved_metadata

    @property
    def _checksums(self):
        if not self._parsed_checksums:
            self._parsed_checksums = self._retrieve_checksums(self._checksums_path)
        return self._parsed_checksums

    @property
    def _files(self):
        if not self._parsed_files:
            self._parsed_files = []
            for file in self._map.describes.files:
                if not is_aggregation(str(file)):
                    if not file.path == self.metadata_path:
                        if not str(file.path).endswith('/'):  # checking for folders, shouldn't have to do this
                            file_checksum_path = file.path.split(self._resource_path, 1)[1].strip("/")
                            file_path = unquote(
                                file_checksum_path.split(
                                    "data/contents/",
                                )[1]
                            )
                            f = File(file_path, unquote(file.path), self._checksums[file_checksum_path])
                            self._parsed_files.append(f)
        return self._parsed_files

    @property
    def _aggregations(self):

        def populate_metadata(_aggr):
            _aggr._metadata

        if not self._parsed_aggregations:
            self._parsed_aggregations = []
            for file in self._map.describes.files:
                if is_aggregation(str(file)):
                    self._parsed_aggregations.append(Aggregation(unquote(file.path), self._hs_session, self._checksums))

            # load metadata for all aggregations (metadata is needed to create any typed aggregation)
            with ThreadPoolExecutor() as executor:
                executor.map(populate_metadata, self._parsed_aggregations)

            # convert aggregations to aggregation type supporting data object
            aggregations_copy = self._parsed_aggregations[:]
            typed_aggregation_classes = {AggregationType.MultidimensionalAggregation: NetCDFAggregation,
                                         AggregationType.TimeSeriesAggregation: TimeseriesAggregation,
                                         AggregationType.GeographicRasterAggregation: GeoRasterAggregation,
                                         AggregationType.GeographicFeatureAggregation: GeoFeatureAggregation,
                                         AggregationType.CSVFileAggregation: CSVAggregation
                                         }
            for aggr in aggregations_copy:
                typed_aggr_cls = typed_aggregation_classes.get(aggr.metadata.type, None)
                if typed_aggr_cls:
                    typed_aggr = typed_aggr_cls.create(base_aggr=aggr)
                    # swapping the generic aggregation with the typed aggregation in the aggregation list
                    self._parsed_aggregations.remove(aggr)
                    self._parsed_aggregations.append(typed_aggr)

        return self._parsed_aggregations

    @property
    def _checksums_path(self):
        path = self.metadata_path.split("/data/", 1)[0]
        path = urljoin(path, "manifest-md5.txt")
        return path

    @property
    def _hsapi_path(self):
        resource_path = self._resource_path
        hsapi_path = urljoin("hsapi", resource_path)
        return hsapi_path

    @property
    def _resource_path(self):
        resource_path = self.metadata_path[: len("/resource/b4ce17c17c654a5c8004af73f2df87ab/")].strip("/")
        return resource_path

    def _retrieve_and_parse(self, path):
        file_str = self._hs_session.retrieve_string(path)
        instance = load_rdf(file_str)
        return instance

    def _retrieve_checksums(self, path):
        file_str = self._hs_session.retrieve_string(path)
        # split string by lines, then split line by delimiter into a dict
        delimiter = "    "
        data = {
            quote(path): checksum for checksum, path in [line.split(delimiter) for line in file_str.split("\n") if line]
        }
        return data

    def _download(self, save_path: str = "", unzip_to: str = None) -> str:
        main_file_path = self.main_file_path

        path = urljoin(self._resource_path, "data", "contents", main_file_path)
        params = {"zipped": "true", "aggregation": "true"}
        path = path.replace('resource', 'django_irods/rest_download', 1)
        downloaded_zip = self._hs_session.retrieve_zip(path, save_path=save_path, params=params)

        if unzip_to:
            import zipfile

            with zipfile.ZipFile(downloaded_zip, 'r') as zip_ref:
                zip_ref.extractall(unzip_to)
            os.remove(downloaded_zip)
            return unzip_to
        return downloaded_zip

    @property
    def metadata_file(self):
        """The path to the metadata file"""
        return self.metadata_path.split("/data/contents/", 1)[1]

    @property
    def metadata(self) -> BaseMetadata:
        """A metadata object for reading and updating metadata values"""
        return self._metadata

    @property
    def metadata_path(self) -> str:
        """The path to the metadata file"""
        return urlparse(str(self._map.describes.is_documented_by)).path

    @property
    def main_file_path(self) -> str:
        """The path to the main file in the aggregation"""
        if self._main_file_path is not None:
            return self._main_file_path
        mft = main_file_type(self.metadata.type)
        if mft:
            for file in self.files():
                if str(file).endswith(mft):
                    self._main_file_path = file.path
                    return self._main_file_path
        if self.metadata.type == AggregationType.FileSetAggregation:
            self._main_file_path = self.files()[0].folder
            return self._main_file_path
        self._main_file_path = self.files()[0].path
        return self._main_file_path

    @refresh
    def save(self) -> None:
        """
        Saves the metadata back to HydroShare
        :return: None
        """
        metadata_file = self.metadata_file
        metadata_string = rdf_string(self._retrieved_metadata, rdf_format="xml")
        url = urljoin(self._hsapi_path, "ingest_metadata")
        self._hs_session.upload_file(url, files={'file': (metadata_file, metadata_string)})

    def files(self, search_aggregations: bool = False, **kwargs) -> List[File]:
        """
        List files and filter by properties on the file object using kwargs (i.e. extension='.txt')
        :param search_aggregations: Defaults False, set to true to search aggregations
        :params **kwargs: Search by properties on the File object (path, name, extension, folder, checksum url)
        :return: a List of File objects matching the filter parameters
        """
        files = self._files
        for key, value in kwargs.items():
            files = list(filter(lambda file: attribute_filter(file, key, value), files))
        if search_aggregations:
            for aggregation in self.aggregations():
                files = files + list(aggregation.files(search_aggregations=search_aggregations, **kwargs))
        return files

    def file(self, search_aggregations=False, **kwargs) -> File:
        """
        Returns a single file in the resource that matches the filtering parameters
        :param search_aggregations: Defaults False, set to true to search aggregations
        :params **kwargs: Search by properties on the File object (path, name, extension, folder, checksum url)
        :return: A File object matching the filter parameters or None if no matching File was found
        """
        files = self.files(search_aggregations=search_aggregations, **kwargs)
        if files:
            return files[0]
        return None

    def aggregations(self, **kwargs) -> List[BaseMetadata]:
        """
        List the aggregations in the resource.  Filter by properties on the metadata object using kwargs.  If you need
        to filter on nested properties, use __ (double underscore) to separate the properties.  For example, to filter
        by the BandInformation name, call this method like aggregations(band_information__name="the name to search").
        :params **kwargs: Search by properties on the metadata object
        :return: a List of Aggregation objects matching the filter parameters
        """
        aggregations = self._aggregations

        for key, value in kwargs.items():
            if key.startswith('file__'):
                file_args = {key[len('file__'):]: value}
                aggregations = [agg for agg in aggregations if agg.files(**file_args)]
            elif key.startswith('files__'):
                file_args = {key[len('files__'):]: value}
                aggregations = [agg for agg in aggregations if agg.files(**file_args)]
            else:
                aggregations = filter(lambda agg: attribute_filter(agg.metadata, key, value), aggregations)
        return list(aggregations)

    def aggregation(self, **kwargs) -> BaseMetadata:
        """
        Returns a single Aggregation in the resource that matches the filtering parameters.  Uses the same filtering
        rules described in the aggregations method.
        :params **kwargs: Search by properties on the metadata object
        :return: An Aggregation object matching the filter parameters or None if no matching Aggregation was found.
        """
        aggregations = self.aggregations(**kwargs)
        if aggregations:
            return aggregations[0]
        return None

    def refresh(self) -> None:
        """
        Forces the retrieval of the resource map and metadata files.  Currently this is implemented to be lazy and will
        only retrieve those files again after another call to access them is made.  This will be later updated to be
        eager and retrieve the files asynchronously.
        """
        # TODO, refresh should destroy the aggregation objects and async fetch everything.
        self._retrieved_map = None
        self._retrieved_metadata = None
        self._parsed_files = None
        self._parsed_aggregations = None
        self._parsed_checksums = None
        self._main_file_path = None

    def delete(self) -> None:
        """Deletes this aggregation from HydroShare"""
        path = urljoin(
            self._hsapi_path,
            "functions",
            "delete-file-type",
            self.metadata.type.value + "LogicalFile",
            self.main_file_path,
        )
        self._hs_session.delete(path, status_code=200)
        self.refresh()


class DataObjectSupportingAggregation(Aggregation):
    """Base class for any aggregation supporting aggregation type specific data manipulation object (e.g. pandas)"""

    @staticmethod
    def create(aggr_cls, base_aggr):
        """Creates a type specific aggregation object from an instance of Aggregation"""
        aggr = aggr_cls(base_aggr._map_path, base_aggr._hs_session, base_aggr._parsed_checksums)
        aggr._retrieved_map = base_aggr._retrieved_map
        aggr._retrieved_metadata = base_aggr._retrieved_metadata
        aggr._parsed_files = base_aggr._parsed_files
        aggr._parsed_aggregations = base_aggr._parsed_aggregations
        aggr._main_file_path = base_aggr._main_file_path
        aggr._data_object = None
        return aggr

    def refresh(self) -> None:
        super().refresh()
        self._data_object = None

    @property
    def data_object(self) -> \
            Union['pandas.DataFrame', 'fiona.Collection', 'rasterio.DatasetReader', 'xarray.Dataset', None]:
        """Returns the data object for the aggregation if the aggregation has been loaded as
        a data object, otherwise None"""
        return self._data_object

    def _get_file_path(self, agg_path):
        main_file_ext = pathlib.Path(self.main_file_path).suffix
        file_name = self.file(extension=main_file_ext).name
        file_path = urljoin(agg_path, file_name)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            file_path = urljoin(file_path, file_name)
            if not os.path.exists(file_path):
                raise Exception(f"Aggregation was not found at: {agg_path}")
        return file_path

    def _validate_aggregation_path(self, agg_path: str, for_save_data: bool = False) -> str:
        return self._get_file_path(agg_path)

    def _get_data_object(self, agg_path: str, func: Callable, **func_kwargs) -> \
            Union['pandas.DataFrame', 'fiona.Collection', 'rasterio.DatasetReader', 'xarray.Dataset']:

        if self._data_object is not None and self.metadata.type != AggregationType.TimeSeriesAggregation:
            return self._data_object

        file_path = self._validate_aggregation_path(agg_path)
        data_object = func(file_path, **func_kwargs)
        if self.metadata.type == AggregationType.MultidimensionalAggregation:
            data_object.load()
            data_object.close()

        # cache the data object for the aggregation
        self._data_object = data_object
        return data_object

    def _validate_aggregation_for_update(self, resource: 'Resource', agg_type: AggregationType) -> None:
        if self.metadata.type != agg_type:
            raise Exception(f"Not a {agg_type.value} aggregation")

        if self._data_object is None:
            raise Exception("No data object exists for this aggregation.")

        # check this aggregation is part of the specified resource
        aggr = resource.aggregation(file__path=self.main_file_path)
        if aggr is None:
            raise Exception("This aggregation is not part of the specified resource.")

    def _compute_updated_aggregation_path(self, temp_folder, *files) -> str:
        file_path = urljoin(temp_folder, os.path.basename(self.main_file_path))
        return file_path

    def _update_aggregation(self, resource, *files):
        temp_folder = uuid4().hex
        resource.folder_create(temp_folder)
        resource.file_upload(*files, destination_path=temp_folder)
        # check aggregation got created in the temp folder
        file_path = self._compute_updated_aggregation_path(temp_folder, *files)
        original_aggr_dir_path = dirname(self.main_file_path)
        aggr = resource.aggregation(file__path=file_path)
        if aggr is not None:
            # delete this aggregation which will be replaced with the updated aggregation
            self.delete()
            # move the aggregation from the temp folder to the location of the deleted aggregation
            resource.aggregation_move(aggr, dst_path=original_aggr_dir_path)

        resource.folder_delete(temp_folder)
        if aggr is None:
            err_msg = f"Failed to update aggregation. Aggregation was not found at: {file_path}"
            raise Exception(err_msg)


class NetCDFAggregation(DataObjectSupportingAggregation):
    """Represents a Multidimensional Aggregation in HydroShare"""

    @classmethod
    def create(cls, base_aggr):
        return super().create(aggr_cls=cls, base_aggr=base_aggr)

    def as_data_object(self, agg_path: str) -> 'xarray.Dataset':
        """
        Loads the Multidimensional aggregation to a xarray Dataset object
        :param agg_path: the path to the Multidimensional aggregation
        :return: the Multidimensional aggregation as a xarray Dataset object
        """
        if xarray is None:
            raise Exception("xarray package was not found")
        return self._get_data_object(agg_path=agg_path, func=xarray.open_dataset)

    def save_data_object(self, resource: 'Resource', agg_path: str, as_new_aggr: bool = False,
                         destination_path: str = "") -> 'Aggregation':
        """
        Saves the xarray Dataset object to the Multidimensional aggregation
        :param resource: the resource containing the aggregation
        :param agg_path: the path to the Multidimensional aggregation
        :param as_new_aggr: Defaults False, set to True to create a new Multidimensional aggregation
        :param destination_path: the destination path in Hydroshare to save the new aggregation
        :return: the updated or new Multidimensional aggregation
        """

        self._validate_aggregation_for_update(resource, AggregationType.MultidimensionalAggregation)
        file_path = self._validate_aggregation_path(agg_path, for_save_data=True)
        self._data_object.to_netcdf(file_path, format="NETCDF4")
        aggr_main_file_path = self.main_file_path
        if not as_new_aggr:
            # cache some of the metadata fields of the original aggregation to update the metadata of the
            # updated aggregation
            keywords = self.metadata.subjects
            additional_meta = self.metadata.additional_metadata

            # upload the updated aggregation files
            self._update_aggregation(resource, file_path)

            # retrieve the updated aggregation
            aggr = resource.aggregation(file__path=aggr_main_file_path)

            # update metadata
            for kw in keywords:
                if kw not in aggr.metadata.subjects:
                    aggr.metadata.subjects.append(kw)
            aggr.metadata.additional_metadata = additional_meta
            aggr.save()
        else:
            # creating a new aggregation
            resource.file_upload(file_path, destination_path=destination_path)

            # retrieve the new aggregation
            agg_path = urljoin(destination_path, os.path.basename(aggr_main_file_path))
            aggr = resource.aggregation(file__path=agg_path)

        aggr._data_object = None
        return aggr


class TimeseriesAggregation(DataObjectSupportingAggregation):
    """Represents a Time Series Aggregation in HydroShare"""
    @classmethod
    def create(cls, base_aggr):
        return super().create(aggr_cls=cls, base_aggr=base_aggr)

    def as_data_object(self, agg_path: str, series_id: str = "") -> 'pandas.DataFrame':
        """
        Loads the Time Series aggregation to a pandas DataFrame object
        :param agg_path: the path to the Time Series aggregation
        :param series_id: the series id of the time series to retrieve
        :return: the Time Series aggregation as a pandas DataFrame object
        """
        if pandas is None:
            raise Exception("pandas package not found")

        def to_series(timeseries_file: str):
            con = sqlite3.connect(timeseries_file)
            return pandas.read_sql(
                f'SELECT * FROM TimeSeriesResultValues WHERE ResultID IN '
                f'(SELECT ResultID FROM Results WHERE ResultUUID = "{series_id}");',
                con,
            ).squeeze()

        return self._get_data_object(agg_path=agg_path, func=to_series)

    def save_data_object(self, resource: 'Resource', agg_path: str, as_new_aggr: bool = False,
                         destination_path: str = "") -> 'Aggregation':

        """
        Saves the pandas DataFrame object to the Time Series aggregation
        :param resource: the resource containing the aggregation
        :param agg_path: the path to the Time Series aggregation
        :param as_new_aggr: Defaults False, set to True to create a new Time Series aggregation
        :param destination_path: the destination path in Hydroshare to save the new aggregation
        :return: the updated or new Time Series aggregation
        """
        self._validate_aggregation_for_update(resource, AggregationType.TimeSeriesAggregation)
        file_path = self._validate_aggregation_path(agg_path, for_save_data=True)
        with closing(sqlite3.connect(file_path)) as conn:
            # write the dataframe to a temp table
            self._data_object.to_sql('temp', conn, if_exists='replace', index=False)
            # delete the matching records from the TimeSeriesResultValues table
            conn.execute("DELETE FROM TimeSeriesResultValues WHERE ResultID IN (SELECT ResultID FROM temp)")
            conn.execute("INSERT INTO TimeSeriesResultValues SELECT * FROM temp")
            # delete the temp table
            conn.execute("DROP TABLE temp")
            conn.commit()

        aggr_main_file_path = self.main_file_path
        data_object = self._data_object
        if not as_new_aggr:
            # cache some of the metadata fields of the original aggregation to update the metadata of the
            # updated aggregation
            keywords = self.metadata.subjects
            additional_meta = self.metadata.additional_metadata
            title = self.metadata.title
            abstract = self.metadata.abstract

            # upload the updated aggregation files to the temp folder - to create the updated aggregation
            self._update_aggregation(resource, file_path)
            # retrieve the updated aggregation
            aggr = resource.aggregation(file__path=aggr_main_file_path)

            # update metadata
            for kw in keywords:
                if kw not in aggr.metadata.subjects:
                    aggr.metadata.subjects.append(kw)
            aggr.metadata.additional_metadata = additional_meta
            aggr.metadata.title = title
            aggr.metadata.abstract = abstract
            aggr.save()
        else:
            # creating a new aggregation by uploading the updated data files
            resource.file_upload(file_path, destination_path=destination_path)

            # retrieve the new aggregation
            agg_path = urljoin(destination_path, os.path.basename(aggr_main_file_path))
            aggr = resource.aggregation(file__path=agg_path)
            data_object = None

        aggr._data_object = data_object
        return aggr


class GeoFeatureAggregation(DataObjectSupportingAggregation):
    """Represents a Geo Feature Aggregation in HydroShare"""
    @classmethod
    def create(cls, base_aggr):
        return super().create(aggr_cls=cls, base_aggr=base_aggr)

    def _validate_aggregation_path(self, agg_path: str, for_save_data: bool = False) -> str:
        if for_save_data:
            for aggr_file in self.files():
                aggr_file = basename(aggr_file)
                if aggr_file.endswith(".shp.xml") or aggr_file.endswith(".sbn") or aggr_file.endswith(".sbx"):
                    # these are optional files for geo feature aggregation
                    continue
                if not os.path.exists(os.path.join(agg_path, aggr_file)):
                    raise Exception(f"Aggregation path '{agg_path}' is not a valid path. "
                                    f"Missing file '{aggr_file}'")
        file_path = self._get_file_path(agg_path)
        return file_path

    def as_data_object(self, agg_path: str) -> 'fiona.Collection':
        """
        Loads the Geo Feature aggregation to a fiona Collection object
        :param agg_path: the path to the Geo Feature aggregation
        :return: the Geo Feature aggregation as a fiona Collection object
        """
        if fiona is None:
            raise Exception("fiona package was not found")
        return self._get_data_object(agg_path=agg_path, func=fiona.open)

    def save_data_object(self, resource: 'Resource', agg_path: str, as_new_aggr: bool = False,
                         destination_path: str = "") -> 'Aggregation':
        """
        Saves the fiona Collection object to the Geo Feature aggregation
        :param resource: the resource containing the aggregation
        :param agg_path: the path to the Geo Feature aggregation
        :param as_new_aggr: Defaults False, set to True to create a new Geo Feature aggregation
        :param destination_path: the destination path in Hydroshare to save the new aggregation
        :return: the updated or new Geo Feature aggregation
        """
        def upload_shape_files(main_file_path, dst_path=""):
            shp_file_dir_path = os.path.dirname(main_file_path)
            filename_starts_with = f"{pathlib.Path(main_file_path).stem}."
            shape_files = []
            for item in os.listdir(shp_file_dir_path):
                if item.startswith(filename_starts_with):
                    file_full_path = os.path.join(shp_file_dir_path, item)
                    shape_files.append(file_full_path)

            if not dst_path:
                self._update_aggregation(resource, *shape_files)
            else:
                resource.file_upload(*shape_files, destination_path=dst_path)

        self._validate_aggregation_for_update(resource, AggregationType.GeographicFeatureAggregation)
        file_path = self._validate_aggregation_path(agg_path, for_save_data=True)
        aggr_main_file_path = self.main_file_path
        data_object = self._data_object
        # need to close the fiona.Collection object to free up access to all the original shape files
        data_object.close()
        if not as_new_aggr:
            # cache some of the metadata fields of the original aggregation to update the metadata of the
            # updated aggregation
            keywords = self.metadata.subjects
            additional_meta = self.metadata.additional_metadata

            # copy the updated shape files to the original shape file location where the user downloaded the
            # aggregation previously
            src_shp_file_dir_path = os.path.dirname(file_path)
            tgt_shp_file_dir_path = os.path.dirname(data_object.path)
            filename_starts_with = f"{pathlib.Path(file_path).stem}."

            for item in os.listdir(src_shp_file_dir_path):
                if item.startswith(filename_starts_with):
                    src_file_full_path = os.path.join(src_shp_file_dir_path, item)
                    tgt_file_full_path = os.path.join(tgt_shp_file_dir_path, item)
                    shutil.copyfile(src_file_full_path, tgt_file_full_path)

            # upload the updated shape files to replace this aggregation
            upload_shape_files(main_file_path=data_object.path)

            # retrieve the updated aggregation
            aggr = resource.aggregation(file__path=aggr_main_file_path)

            # update aggregation metadata
            for kw in keywords:
                if kw not in aggr.metadata.subjects:
                    aggr.metadata.subjects.append(kw)
            aggr.metadata.additional_metadata = additional_meta
            aggr.save()
        else:
            # upload the updated shape files to create a new geo feature aggregation
            upload_shape_files(main_file_path=file_path, dst_path=destination_path)

            # retrieve the new aggregation
            agg_path = urljoin(destination_path, os.path.basename(aggr_main_file_path))
            aggr = resource.aggregation(file__path=agg_path)

        aggr._data_object = None
        return aggr


class GeoRasterAggregation(DataObjectSupportingAggregation):
    """Represents a Geo Raster Aggregation in HydroShare"""
    @classmethod
    def create(cls, base_aggr):
        return super().create(aggr_cls=cls, base_aggr=base_aggr)

    def _compute_updated_aggregation_path(self, temp_folder, *files) -> str:
        file_path = ""
        for _file in files:
            filename = os.path.basename(_file)
            if filename.endswith(".vrt"):
                file_path = urljoin(temp_folder, filename)
                break
            else:
                filename = pathlib.Path(filename).stem + ".vrt"
                file_path = urljoin(temp_folder, filename)
                break
        return file_path

    def _validate_aggregation_path(self, agg_path: str, for_save_data: bool = False) -> str:
        if for_save_data:
            tif_file_count = 0
            vrt_file_count = 0
            tif_file_path = ""
            vrt_file_path = ""
            for item in os.listdir(agg_path):
                item_full_path = os.path.join(agg_path, item)
                if os.path.isfile(item_full_path):
                    file_ext = pathlib.Path(item_full_path).suffix.lower()
                    if file_ext in (".tif", ".tiff"):
                        tif_file_count += 1
                        tif_file_path = item_full_path
                    elif file_ext == '.vrt':
                        vrt_file_path = item_full_path
                        vrt_file_count += 1
                        if vrt_file_count > 1:
                            raise Exception(f"Aggregation path '{agg_path}' is not a valid path. "
                                            f"More than one vrt was file found")
                    else:
                        raise Exception(f"Aggregation path '{agg_path}' is not a valid path. "
                                        f"There are files that are not of raster file types")
            if tif_file_count == 0:
                raise Exception(f"Aggregation path '{agg_path}' is not a valid path. "
                                f"No tif file was found")
            if tif_file_count > 1 and vrt_file_count == 0:
                raise Exception(f"Aggregation path '{agg_path}' is not a valid path. "
                                f"Missing a vrt file")
            if vrt_file_path:
                file_path = vrt_file_path
            else:
                file_path = tif_file_path
        else:
            file_path = self._get_file_path(agg_path)

        return file_path

    def as_data_object(self, agg_path: str) -> 'rasterio.DatasetReader':
        """
        Loads the Geo Raster aggregation to a rasterio DatasetReader object
        :param agg_path: the path to the Geo Raster aggregation
        :return: the Geo Raster aggregation as a rasterio DatasetReader object
        """
        if rasterio is None:
            raise Exception("rasterio package was not found")
        return self._get_data_object(agg_path=agg_path, func=rasterio.open)

    def save_data_object(self, resource: 'Resource', agg_path: str, as_new_aggr: bool = False,
                         destination_path: str = "") -> 'Aggregation':
        """
        Saves the rasterio DatasetReader object to the Geo Raster aggregation
        :param resource: the resource containing the aggregation
        :param agg_path: the path to the Geo Raster aggregation
        :param as_new_aggr: Defaults False, set to True to create a new Geo Raster aggregation
        :param destination_path: the destination path in Hydroshare to save the new aggregation
        :return: the updated or new Geo Raster aggregation
        """
        def upload_raster_files(dst_path=""):
            raster_files = []
            for item in os.listdir(agg_path):
                item_full_path = os.path.join(agg_path, item)
                if os.path.isfile(item_full_path):
                    raster_files.append(item_full_path)

            if not dst_path:
                self._update_aggregation(resource, *raster_files)
            else:
                resource.file_upload(*raster_files, destination_path=dst_path)

        def get_main_file_path():
            main_file_name = os.path.basename(file_path)
            if not main_file_name.lower().endswith('.vrt'):
                main_file_name = pathlib.Path(main_file_name).stem + ".vrt"
            if destination_path:
                aggr_main_file_path = os.path.join(destination_path, main_file_name)
            else:
                aggr_main_file_path = main_file_name
            return aggr_main_file_path

        self._validate_aggregation_for_update(resource, AggregationType.GeographicRasterAggregation)
        file_path = self._validate_aggregation_path(agg_path, for_save_data=True)
        if not as_new_aggr:
            destination_path = dirname(self.main_file_path)

            # cache some of the metadata fields of the original aggregation to update the metadata of the
            # updated aggregation
            keywords = self.metadata.subjects
            additional_meta = self.metadata.additional_metadata
            upload_raster_files(dst_path=destination_path)

            aggr_main_file_path = get_main_file_path()
            # retrieve the updated aggregation
            aggr = resource.aggregation(file__path=aggr_main_file_path)

            # update metadata
            for kw in keywords:
                if kw not in aggr.metadata.subjects:
                    aggr.metadata.subjects.append(kw)
            aggr.metadata.additional_metadata = additional_meta
            aggr.save()
        else:
            # creating a new aggregation by uploading the updated data files
            upload_raster_files(dst_path=destination_path)

            # retrieve the new aggregation
            aggr_main_file_path = get_main_file_path()
            agg_path = urljoin(destination_path, os.path.basename(aggr_main_file_path))
            aggr = resource.aggregation(file__path=agg_path)

        aggr._data_object = None
        return aggr


class CSVAggregation(DataObjectSupportingAggregation):
    """Represents a CSV Aggregation in HydroShare"""
    @classmethod
    def create(cls, base_aggr):
        return super().create(aggr_cls=cls, base_aggr=base_aggr)

    def as_data_object(self, agg_path: str) -> 'pandas.DataFrame':
        """
        Loads the CSV aggregation to a pandas DataFrame object
        :param agg_path: the path to the Time Series aggregation
        :return: the CSV aggregation as a pandas DataFrame object
        """
        if pandas is None:
            raise Exception("pandas package not found")

        return self._get_data_object(agg_path=agg_path, func=pandas.read_csv, comment="#", dtype="string",
                                     engine="python")

    def save_data_object(self, resource: 'Resource', agg_path: str, as_new_aggr: bool = False,
                         destination_path: str = "") -> 'Aggregation':

        """
        Saves the pandas DataFrame object to the CSV aggregation
        :param resource: the resource containing the aggregation
        :param agg_path: the path to the CSV aggregation
        :param as_new_aggr: Defaults False, set to True to create a new CSV aggregation
        :param destination_path: the destination path in Hydroshare to save the new aggregation
        :return: the updated or new CSV aggregation
        """
        self._validate_aggregation_for_update(resource, AggregationType.CSVFileAggregation)
        file_path = self._validate_aggregation_path(agg_path, for_save_data=True)
        self._data_object.to_csv(file_path, index=False)
        aggr_main_file_path = self.main_file_path
        data_object = self._data_object
        if not as_new_aggr:
            # cache some of the metadata fields of the original aggregation to update the metadata of the
            # updated aggregation
            keywords = self.metadata.subjects
            additional_meta = self.metadata.additional_metadata
            title = self.metadata.title

            # upload the updated aggregation files to the temp folder - to create the updated aggregation
            self._update_aggregation(resource, file_path)
            # retrieve the updated aggregation
            aggr = resource.aggregation(file__path=aggr_main_file_path)

            # update metadata
            for kw in keywords:
                if kw not in aggr.metadata.subjects:
                    aggr.metadata.subjects.append(kw)
            aggr.metadata.additional_metadata = additional_meta
            aggr.metadata.title = title
            aggr.save()
        else:
            # creating a new aggregation by uploading the updated data files
            resource.file_upload(file_path, destination_path=destination_path)

            # retrieve the new aggregation
            agg_path = urljoin(destination_path, os.path.basename(aggr_main_file_path))
            aggr = resource.aggregation(file__path=agg_path)
            data_object = None

        aggr._data_object = data_object
        return aggr


class Resource(Aggregation):
    """Represents a Resource in HydroShare"""

    @property
    def _hsapi_path(self):
        path = urlparse(str(self.metadata.identifier)).path
        return '/hsapi' + path

    def _upload(self, file, destination_path):
        path = urljoin(self._hsapi_path, "files", destination_path.strip("/"))
        self._hs_session.upload_file(path, files={'file': open(file, 'rb')}, status_code=201)

    def _delete_file(self, path) -> None:
        path = urljoin(self._hsapi_path, "files", path)
        self._hs_session.delete(path, status_code=200)

    def _download_file_folder(self, path: str, save_path: str) -> None:
        return self._hs_session.retrieve_zip(path, save_path)

    def _delete_file_folder(self, path: str) -> None:
        path = urljoin(self._hsapi_path, "folders", path)
        self._hs_session.delete(path, status_code=200)

    # system information

    @property
    def resource_id(self) -> str:
        """The resource id (guid) of the HydroShare resource"""
        return self._map.identifier

    @property
    def metadata_file(self):
        """The path to the metadata file"""
        return self.metadata_path.split("/data/", 1)[1]

    def system_metadata(self):
        """
        The system metadata associated with the HydroShare resource
        returns: JSON object
        """
        hsapi_path = urljoin(self._hsapi_path, 'sysmeta')
        return self._hs_session.get(hsapi_path, status_code=200).json()

    # access operations

    def set_sharing_status(self, public: bool):
        """
        Set the sharing status of the resource to public or private
        :param public: bool, set to True for public, False for private
        """
        path = urljoin("hsapi", "resource", "accessRules", self.resource_id)
        data = {'public': public}
        self._hs_session.put(path, status_code=200, data=data)

    @property
    def access_permission(self):
        """
        Retrieves the access permissions of the resource
        :return: JSON object
        """
        path = urljoin(self._hsapi_path, "access")
        response = self._hs_session.get(path, status_code=200)
        return response.json()

    # resource operations

    def new_version(self):
        """
        Creates a new version of the resource on HydroShare
        :return: A Resource object of the newly created resource version
        """
        path = urljoin(self._hsapi_path, "version")
        response = self._hs_session.post(path, status_code=202)
        resource_id = response.text
        return Resource("/resource/{}/data/resourcemap.xml".format(resource_id), self._hs_session)

    def copy(self):
        """
        Copies this Resource into a new resource on HydroShare
        returns: A Resource object of the newly copied resource
        """
        path = urljoin(self._hsapi_path, "copy")
        response = self._hs_session.post(path, status_code=202)
        resource_id = response.text
        return Resource("/resource/{}/data/resourcemap.xml".format(resource_id), self._hs_session)

    def download(self, save_path: str = "") -> str:
        """
        Downloads a zipped bagit archive of the resource from HydroShare
        param save_path: A local path to save the bag to, defaults to the current working directory
        returns: The relative pathname of the download
        """
        return self._hs_session.retrieve_bag(self._hsapi_path, save_path=save_path)

    @refresh
    def delete(self) -> None:
        """
        Deletes the resource on HydroShare
        :return: None
        """
        hsapi_path = self._hsapi_path
        self._hs_session.delete(hsapi_path, status_code=204)

    @refresh
    def save(self) -> None:
        """
        Saves the metadata to HydroShare
        :return: None
        """
        metadata_string = rdf_string(self._retrieved_metadata, rdf_format="xml")
        path = urljoin(self._hsapi_path, "ingest_metadata")
        self._hs_session.upload_file(path, files={'file': ('resourcemetadata.xml', metadata_string)})

    # referenced content operations

    @refresh
    def reference_create(self, file_name: str, url: str, path: str = '') -> None:
        """
        Creates a HydroShare reference object to reference content outside of the resource
        :param file_name: the file name of the resulting .url file
        :param url: the url of the referenced content
        :param path: the path to create the reference in
        :return: None
        """
        request_path = urljoin(self._hsapi_path.replace(self.resource_id, ""), "data-store-add-reference")
        self._hs_session.post(
            request_path,
            data={"res_id": self.resource_id, "curr_path": path, "ref_name": file_name, "ref_url": url},
            status_code=200,
        )

    @refresh
    def reference_update(self, file_name: str, url: str, path: str = '') -> None:
        """
        Updates a HydroShare reference object
        :param file_name: the file name for the .url file
        :param url: the url of the referenced content
        :param path: the path to the directory where the reference is located
        :return: None
        """
        request_path = urljoin(self._hsapi_path.replace(self.resource_id, ""), "data_store_edit_reference_url")
        self._hs_session.post(
            request_path,
            data={"res_id": self.resource_id, "curr_path": path, "url_filename": file_name, "new_ref_url": url},
            status_code=200,
        )

    # file operations

    @refresh
    def folder_create(self, folder: str) -> None:
        """
        Creates a folder on HydroShare
        :param folder: the folder path to create
        :return: None
        """
        path = urljoin(self._hsapi_path, "folders", folder)
        self._hs_session.put(path, status_code=201)

    @refresh
    def folder_rename(self, path: str, new_path: str) -> None:
        """
        Renames a folder on HydroShare
        :param path: the path to the folder to rename
        :param new_path: the new path folder name
        :return: None
        """
        self.file_rename(path=path, new_path=new_path)

    @refresh
    def folder_delete(self, path: str = None) -> None:
        """
        Deletes a folder on HydroShare
        :param path: the path to the folder
        :return: None
        """
        self._delete_file_folder(path)

    def folder_download(self, path: str, save_path: str = ""):
        """
        Downloads a folder from HydroShare
        :param path: The path to folder
        :param save_path: The local path to save the download to, defaults to the current directory
        :return: The path to the download zipped folder
        """
        return self._hs_session.retrieve_zip(
            urljoin(self._resource_path, "data", "contents", path), save_path, params={"zipped": "true"}
        )

    def file_download(self, path: str, save_path: str = "", zipped: bool = False):
        """
        Downloads a file from HydroShare
        :param path: The path to the file
        :param save_path: The local path to save the file to
        :param zipped: Defaults to False, set to True to download the file zipped
        :return: The path to the downloaded file
        """
        if zipped:
            return self._hs_session.retrieve_zip(
                urljoin(self._resource_path, "data", "contents", path), save_path, params={"zipped": "true"}
            )
        else:
            return self._hs_session.retrieve_file(urljoin(self._resource_path, "data", "contents", path), save_path)

    @refresh
    def file_delete(self, path: str = None) -> None:
        """
        Delete a file on HydroShare
        :param path: The path to the file
        :return: None
        """
        self._delete_file(path)

    @refresh
    def file_rename(self, path: str, new_path: str) -> None:
        """
        Rename a file on HydroShare
        :param path: The path to the file
        :param new_path: the renamed path to the file
        :return: None
        """
        rename_path = urljoin(self._hsapi_path, "functions", "move-or-rename")
        self._hs_session.post(rename_path, status_code=200, data={"source_path": path, "target_path": new_path})

    @refresh
    def file_zip(self, path: str, zip_name: str = None, remove_file: bool = True) -> None:
        """
        Zip a file on HydroShare
        :param path: The path to the file
        :param zip_name: The name of the zipped file
        :param remove_file: Defaults to True, set to False to not delete the file that was zipped
        :return: None
        """
        zip_name = basename(path) + ".zip" if not zip_name else zip_name
        data = {"input_coll_path": path, "output_zip_file_name": zip_name, "remove_original_after_zip": remove_file}
        zip_path = urljoin(self._hsapi_path, "functions", "zip")
        self._hs_session.post(zip_path, status_code=200, data=data)

    @refresh
    def file_unzip(self, path: str, overwrite: bool = True, ingest_metadata=True) -> None:
        """
        Unzips a file on HydroShare
        :param path: The path to the file to unzip
        :param overwrite: Defaults to True, set to False to unzip the files into a folder with the zip filename
        :param ingest_metadata: Defaults to True, set to False to not ingest HydroShare RDF metadata xml files
        :return: None
        """
        if not path.endswith(".zip"):
            raise Exception("File {} is not a zip, and cannot be unzipped".format(path))
        unzip_path = urljoin(self._hsapi_path, "functions", "unzip", "data", "contents", path)
        self._hs_session.post(
            unzip_path, status_code=200, data={"overwrite": overwrite, "ingest_metadata": ingest_metadata}
        )

    def file_aggregate(self, path: str, agg_type: AggregationType, refresh: bool = True):
        """
        Aggregate a file to a HydroShare aggregation type.  Aggregating files allows you to specify metadata specific
        to the files associated with the aggregation.  To set a FileSet aggregation, include the path to the folder or
        a file in the folder you would like to create a FileSet aggregation from.
        :param path: The path to the file to aggregate
        :param agg_type: The AggregationType to create
        :param refresh: Defaults True, toggles automatic refreshing of the updated resource in HydroShare
        :return: The newly created Aggregation object if refresh is True
        """
        type_value = agg_type.value
        data = {}
        if agg_type == AggregationType.SingleFileAggregation:
            type_value = 'SingleFile'
        if agg_type == AggregationType.FileSetAggregation:
            if '/' in path:
                relative_path = dirname(path)
            else:
                relative_path = path
            data = {"folder_path": relative_path}

        url = urljoin(self._hsapi_path, "functions", "set-file-type", path, type_value)
        self._hs_session.post(url, status_code=201, data=data)
        if refresh:
            # Only return the newly created aggregation if a refresh is requested
            self.refresh()
            return self.aggregation(file__path=path)

    @refresh
    def file_upload(self, *files: str, destination_path: str = "") -> None:
        """
        Uploads files to a folder in HydroShare
        :param *files: The local file paths to upload
        :param destination_path: The path on HydroShare to upload the files to, defaults to the root contents directory
        :return: None
        """
        if len(files) == 1:
            self._upload(files[0], destination_path=destination_path)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                zipped_file = os.path.join(tmpdir, 'files.zip')
                with ZipFile(zipped_file, 'w') as zipped:
                    for file in files:
                        zipped.write(file, os.path.basename(file))
                self._upload(zipped_file, destination_path=destination_path)
                unzip_path = urljoin(
                    self._hsapi_path, "functions", "unzip", "data", "contents", destination_path, 'files.zip'
                )
                self._hs_session.post(
                    unzip_path, status_code=200, data={"overwrite": "true", "ingest_metadata": "true"}
                )
        # TODO, return those files?

    # aggregation operations

    @refresh
    def aggregation_remove(self, aggregation: Aggregation) -> None:
        """
        Removes an aggregation from HydroShare.  This does not remove the files in the aggregation.
        :param aggregation: The aggregation object to remove
        :return: None
        """
        path = urljoin(
            aggregation._hsapi_path,
            "functions",
            "remove-file-type",
            aggregation.metadata.type.value + "LogicalFile",
            aggregation.main_file_path,
        )
        aggregation._hs_session.post(path, status_code=200)
        aggregation.refresh()

    @refresh
    def aggregation_move(self, aggregation: Aggregation, dst_path: str = "") -> None:
        """
        Moves an aggregation from its current location to another folder in HydroShare.
        :param aggregation: The aggregation object to move
        :param  dst_path: The target file path to move the aggregation to - target folder must exist
        :return: None
        """
        path = urljoin(
            aggregation._hsapi_path,
            aggregation.metadata.type.value + "LogicalFile",
            aggregation.main_file_path,
            "functions",
            "move-file-type",
            dst_path,
        )
        response = aggregation._hs_session.post(path, status_code=200)
        json_response = response.json()
        task_id = json_response['id']
        status = json_response['status']
        if status in ("Not ready", "progress"):
            while aggregation._hs_session.check_task(task_id) != 'true':
                time.sleep(CHECK_TASK_PING_INTERVAL)
        aggregation.refresh()

    @refresh
    def aggregation_delete(self, aggregation: Aggregation) -> None:
        """
        Deletes an aggregation from HydroShare.  This deletes the files and metadata in the aggregation.
        :param aggregation: The aggregation object to delete
        :return: None
        """
        aggregation.delete()

    def aggregation_download(self, aggregation: Aggregation, save_path: str = "", unzip_to: str = None) -> str:
        """
        Download an aggregation from HydroShare
        :param aggregation: The aggregation to download
        :param save_path: The local path to save the aggregation to, defaults to the current directory
        :param unzip_to: If set, the resulting download will be unzipped to the specified path
        :return: None
        """
        return aggregation._download(save_path=save_path, unzip_to=unzip_to)


class HydroShareSession:
    def __init__(
        self,
        host,
        protocol,
        port,
        *,
        username: str = None,
        password: str = None,
        client_id: str = None,
        token: Union[Token, Dict[str, str]] = None,
    ):
        self._host = host
        self._protocol = protocol
        self._port = port
        self._client_id = client_id
        self._token = token
        if client_id or token:
            if not token or not client_id:
                raise ValueError("Oauth2 requires both token and client_id be provided")
            else:
                token = self._validate_oauth2_token(token)
                self._session = OAuth2Session(client_id=client_id, token=token)
        else:
            self._session = requests.Session()
            default_agent = self._session.headers['User-Agent']
            self._session.headers['User-Agent'] = default_agent + ' (hsclient)'

            if username is None or password is None:
                return

            self.set_auth((username, password))

    def set_auth(self, auth):
        if self._client_id:
            raise NotImplementedError(f"This session is an Oauth2 session and does not provide the set_oauth method")
        self._session.auth = auth

    def set_oauth(self, client_id: str, token: Union[Token, Dict[str, str]]):
        token = self._validate_oauth2_token(token)
        self._session = OAuth2Session(client_id=client_id, token=token)

    @property
    def host(self):
        return self._host

    @property
    def base_url(self):
        return "{}://{}:{}".format(self._protocol, self._host, self._port)

    def _build_url(self, path: str):
        path = "/" + path.strip("/") + "/"
        return self.base_url + path

    def retrieve_string(self, path):
        file = self.get(path, status_code=200, allow_redirects=True)
        return file.content.decode()

    def retrieve_file(self, path, save_path=""):
        file = self.get(path, status_code=200, allow_redirects=True)
        cd = file.headers['content-disposition']
        filename = urllib.parse.unquote(cd.split("filename=")[1].strip('"'))
        downloaded_file = os.path.join(save_path, filename)
        with open(downloaded_file, 'wb') as f:
            f.write(file.content)
        return downloaded_file

    def retrieve_bag(self, path, save_path=""):
        file = self.get(path, status_code=200, allow_redirects=True)

        if file.headers['Content-Type'] != "application/zip":
            time.sleep(CHECK_TASK_PING_INTERVAL)
            return self.retrieve_bag(path, save_path)
        return self.retrieve_file(path, save_path)

    def check_task(self, task_id):
        response = self.get(f"/hsapi/taskstatus/{task_id}/", status_code=200)
        return response.json()['status']

    def retrieve_zip(self, path, save_path="", params=None):
        if params is None:
            params = {}
        file = self.get(path, status_code=200, allow_redirects=True, params=params)
        json_response = file.json()
        task_id = json_response['task_id']
        download_path = json_response['download_path']
        zip_status = json_response['zip_status']
        if zip_status == "Not ready":
            while self.check_task(task_id) != 'true':
                time.sleep(CHECK_TASK_PING_INTERVAL)
        return self.retrieve_file(download_path, save_path)

    def upload_file(self, path, files, status_code=204):
        return self.post(path, files=files, status_code=status_code)

    def post(self, path, status_code, data=None, params={}, **kwargs):
        url = encode_resource_url(self._build_url(path))
        response = self._session.post(url, params=params, data=data, **kwargs)
        if response.status_code != status_code:
            raise Exception(
                "Failed POST {}, status_code {}, message {}".format(url, response.status_code, response.content)
            )
        return response

    def put(self, path, status_code, data=None, **kwargs):
        url = encode_resource_url(self._build_url(path))
        response = self._session.put(url, data=data, **kwargs)
        if response.status_code != status_code:
            raise Exception(
                "Failed PUT {}, status_code {}, message {}".format(url, response.status_code, response.content)
            )
        return response

    def get(self, path, status_code, **kwargs):
        url = encode_resource_url(self._build_url(path))
        response = self._session.get(url, **kwargs)
        if response.status_code != status_code:
            raise Exception(
                "Failed GET {}, status_code {}, message {}".format(url, response.status_code, response.content)
            )
        return response

    def delete(self, path, status_code, **kwargs):
        url = encode_resource_url(self._build_url(path))
        response = self._session.delete(url, **kwargs)
        if response.status_code != status_code:
            raise Exception(
                "Failed DELETE {}, status_code {}, message {}".format(url, response.status_code, response.content)
            )
        return response

    @staticmethod
    def _validate_oauth2_token(token: Union[Token, Dict[str, str]]) -> dict:
        """Validate that object follows OAuth2 token specification. return dictionary representation
        of OAuth2 token dropping optional fields that are None."""
        if isinstance(token, dict) or isinstance(token, Token):
            # try to coerce into Token model
            o = Token.model_validate(token)
            # drop None fields from output
            return o.model_dump(exclude_none=True)
        else:
            error_message = "token must be hsclient.Token or dictionary following schema:\n" "{}".format(
                pformat(Token.__annotations__, sort_dicts=False)
            )
            raise ValueError(error_message)


class HydroShare:
    """
    A HydroShare object for querying HydroShare's REST API.  Provide a username and password at initialization or call
    the sign_in() method to prompt for the username and password.

    If using OAuth2 is desired, provide the client_id and token to use.  If on CUAHSI JupyterHub or another JupyterHub
    environment that authenticates with Hydroshare, call the hs_juptyerhub() method to read the credentials from
    Jupyterhub.

    :param username: A HydroShare username
    :param password: A HydroShare password associated with the username
    :param host: The host to use, defaults to `www.hydroshare.org`
    :param protocol: The protocol to use, defaults to `https`
    :param port: The port to use, defaults to `443`
    :param client_id: The client id associated with the OAuth2 token
    :param token: The OAuth2 token to use
    """

    default_host = 'www.hydroshare.org'
    default_protocol = "https"
    default_port = 443

    def __init__(
        self,
        username: str = None,
        password: str = None,
        host: str = default_host,
        protocol: str = default_protocol,
        port: int = default_port,
        client_id: str = None,
        token: Union[Token, Dict[str, str]] = None,
    ):
        if client_id or token:
            if not client_id or not token:
                raise ValueError("Oauth2 requires a client_id to be paired with a token")
            else:
                self._hs_session = HydroShareSession(
                    host=host, protocol=protocol, port=port, client_id=client_id, token=token
                )
                self.my_user_info()  # validate credentials
        else:
            self._hs_session = HydroShareSession(
                username=username, password=password, host=host, protocol=protocol, port=port
            )
            if username or password:
                self.my_user_info()  # validate credentials

        self._resource_object_cache: Dict[str, Resource] = dict()

    def sign_in(self) -> None:
        """Prompts for username/password.  Useful for avoiding saving your HydroShare credentials to a notebook"""
        username = input("Username: ").strip()
        password = getpass.getpass("Password for {}: ".format(username))
        self._hs_session.set_auth((username, password))
        self.my_user_info()  # validate credentials

    @classmethod
    def hs_juptyerhub(cls, hs_auth_path="/home/jovyan/data/.hs_auth"):
        """
        Create a new HydroShare object using OAuth2 credentials stored in a canonical CUAHSI
        Jupyterhub OAuth2 pickle file (stored at :param hs_auth_path:).

        Provide a non-default (default: `/home/jovyan/data/.hs_auth`) path to the hs_auth file with
        :param hs_auth_path:.
        """
        if not os.path.isfile(hs_auth_path):
            raise ValueError(f"hs_auth_path {hs_auth_path} does not exist.")
        with open(hs_auth_path, 'rb') as f:
            token, client_id = pickle.load(f)
        instance = cls(client_id=client_id, token=token)
        instance.my_user_info()  # validate credentials
        return instance

    def search(
        self,
        creator: str = None,
        contributor: str = None,
        owner: str = None,
        group_name: str = None,
        from_date: datetime = None,
        to_date: datetime = None,
        edit_permission: bool = False,
        resource_types: List[str] = [],
        subject: List[str] = [],
        full_text_search: str = None,
        published: bool = False,
        spatial_coverage: Union[BoxCoverage, PointCoverage] = None,
    ):
        """
        Query the GET /hsapi/resource/ REST end point of the HydroShare server.
        :param creator: Filter results by the HydroShare username or email
        :param author: Filter results by the HydroShare username or email
        :param owner: Filter results by the HydroShare username or email
        :param group_name: Filter results by the HydroShare group name associated with resources
        :param from_date: Filter results to those created after from_date.  Must be datetime.date.
        :param to_date: Filter results to those created before to_date.  Must be datetime.date.  Because dates have
            no time information, you must specify date+1 day to get results for date (e.g. use 2015-05-06 to get
            resources created up to and including 2015-05-05)
        :param types: Filter results to particular HydroShare resource types (Deprecated, all types are Composite)
        :param subject: Filter by comma separated list of subjects
        :param full_text_search: Filter by full text search
        :param edit_permission: Filter by boolean edit permission
        :param published: Filter by boolean published status
        :param spatial_coverage: Filtering by spatial coverage raises a 500, do not use

        :return: A generator to iterate over a ResourcePreview object
        """

        params = {"edit_permission": edit_permission, "published": published}
        if creator:
            params["creator"] = creator
        if contributor:
            params["author"] = contributor
        if owner:
            params["owner"] = owner
        if group_name:
            params["group"] = group_name
        if resource_types:
            params["type[]"] = resource_types
        if subject:
            params["subject"] = ",".join(subject)
        if full_text_search:
            params["full_text_search"] = full_text_search
        if from_date:
            params["from_date"] = from_date.strftime('%Y-%m-%d')
        if to_date:
            params["to_date"] = to_date.strftime('%Y-%m-%d')
        if spatial_coverage:
            yield Exception(
                "Bad Request, status_code 400, spatial_coverage queries are disabled."
            )
            # TODO: re-enable after resolution of https://github.com/hydroshare/hydroshare/issues/5240
            # params["coverage_type"] = spatial_coverage.type
            # if spatial_coverage.type == "point":
            #     params["north"] = spatial_coverage.north
            #     params["east"] = spatial_coverage.east
            # else:
            #     params["north"] = spatial_coverage.northlimit
            #     params["east"] = spatial_coverage.eastlimit
            #     params["south"] = spatial_coverage.southlimit
            #     params["west"] = spatial_coverage.westlimit
        response = self._hs_session.get("/hsapi/resource/", 200, params=params)

        res = response.json()
        results = res['results']
        for item in results:
            yield ResourcePreview(**item)

        while res['next']:
            next_url = res['next']
            next_url = urlparse(next_url)
            path = next_url.path
            params = next_url.query
            response = self._hs_session.get(path, 200, params=params)
            res = response.json()
            results = res['results']
            for item in results:
                yield ResourcePreview(**item)

    def resource(self, resource_id: str, validate: bool = True, use_cache: bool = True) -> Resource:
        """
        Creates a resource object from HydroShare with the provided resource_id
        :param resource_id: The resource id of the resource to retrieve
        :param validate: Defaults to True, set to False to not validate the resource exists
        :param use_cache: Defaults to True, set to False to skip the cache, and always retrieve the
            resource from HydroShare. This parameter also does not cache the retrieved Resource
            object.
        :return: A Resource object representing a resource on HydroShare
        """
        if resource_id in self._resource_object_cache and use_cache:
            return self._resource_object_cache[resource_id]

        res = Resource("/resource/{}/data/resourcemap.xml".format(resource_id), self._hs_session)
        if validate:
            res.metadata

        if use_cache:
            self._resource_object_cache[resource_id] = res
        return res

    def create(self, use_cache: bool = True) -> Resource:
        """
        Creates a new resource on HydroShare
        :param use_cache: Defaults to True, set to False to skip the cache, and always retrieve the
            resource from HydroShare. This parameter also does not cache the retrieved Resource
            object.
        :return: A Resource object representing a resource on HydroShare
        """
        response = self._hs_session.post('/hsapi/resource/', status_code=201)
        resource_id = response.json()['resource_id']
        return self.resource(resource_id, use_cache=use_cache)

    def user(self, user_id: int) -> User:
        """
        Retrieves the user details of a Hydroshare user
        :param user_id: The user id of the user details to retrieve
        :return: User object representing the user details
        """
        response = self._hs_session.get(f'/hsapi/userDetails/{user_id}/', status_code=200)
        return User(**response.json())

    def my_user_info(self):
        """
        Retrieves the user info of the user's credentials provided
        :return: JSON object representing the user info
        """
        response = self._hs_session.get('/hsapi/userInfo/', status_code=200)
        return response.json()
