# Geographic Feature Aggregation Metadata

## Properties

- **`title`** *(string)*: A string containing a descriptive title for the aggregation. Default: `null`.
- **`subjects`** *(array)*: A list of keyword strings expressing the topic of the aggregation. Default: `[]`.
    - **Items** *(string)*
- **`language`** *(string)*: The 3-character string for the language in which the metadata and content are expressed. Default: `"eng"`.
- **`additional_metadata`** *(array)*: A dictionary of additional metadata elements expressed as key-value pairs.
    - **Items** *(object)*: A key-value pair. Default: `[]`.
        - **`key`** *(string)*
        - **`value`** *(string)*
- **`spatial_coverage`**: An object containing the geospatial coverage for the aggregation expressed as either a bounding box or point. Default: `null`.
    - **Any of**
        - : Refer to *[#/definitions/PointCoverage](#definitions/PointCoverage)*.
        - : Refer to *[#/definitions/BoxCoverage](#definitions/BoxCoverage)*.
- **`period_coverage`**: An object containing the temporal coverage for a aggregation expressed as a date range. Default: `null`.
    - **Any of**
        - : Refer to *[#/definitions/PeriodCoverage](#definitions/PeriodCoverage)*.
        - *null*
- **`field_information`** *(array)*: A list of objects containing information about the fields in the dataset attribute table. Default: `[]`.
    - **Items**: Refer to *[#/definitions/FieldInformation](#definitions/FieldInformation)*.
- **`geometry_information`**: An object containing information about the geometry of the features in the dataset.
    - **All of**
        - : Refer to *[#/definitions/GeometryInformation](#definitions/GeometryInformation)*.
- **`spatial_reference`**: An object containing spatial reference information for the dataset. Default: `null`.
    - **Any of**
        - : Refer to *[#/definitions/BoxSpatialReference](#definitions/BoxSpatialReference)*.
        - : Refer to *[#/definitions/PointSpatialReference](#definitions/PointSpatialReference)*.
- **`type`**: A string expressing the aggregation type from the list of HydroShare aggregation types. Default: `"GeoFeature"`.
    - **All of**
        - : Refer to *[#/definitions/AggregationType](#definitions/AggregationType)*.
- **`url`** *(string, format: uri, required)*: An object containing the URL of the aggregation.
- **`rights`**: An object containing information about the rights held in and over the aggregation and the license under which a aggregation is shared. Default: `null`.
    - **Any of**
        - : Refer to *[#/definitions/Rights](#definitions/Rights)*.
        - *null*
## Definitions

- <a id="definitions/AggregationType"></a>**`AggregationType`** *(string)*: Must be one of: `["Generic", "FileSet", "GeoRaster", "NetCDF", "GeoFeature", "RefTimeseries", "TimeSeries", "ModelProgram", "ModelInstance", "CSV"]`.
- <a id="definitions/BoxCoverage"></a>**`BoxCoverage`** *(object)*: A class used to represent geographic coverage metadata for a resource or aggregation expressed as a
latitude-longitude bounding box.
    - **`type`** *(string)*: A string containing the type of geographic coverage. Must be one of: `["box"]`. Must be: `"box"`. Default: `"box"`.
    - **`name`** *(string)*: A string containing a name for the place associated with the geographic coverage. Default: `null`.
    - **`northlimit`** *(number, required)*: A floating point value containing the constant coordinate for the northernmost face or edge of the bounding box. Exclusive minimum: `-90.0`. Exclusive maximum: `90.0`.
    - **`eastlimit`** *(number, required)*: A floating point value containing the constant coordinate for the easternmost face or edge of the bounding box. Exclusive minimum: `-180.0`. Exclusive maximum: `180.0`.
    - **`southlimit`** *(number, required)*: A floating point value containing the constant coordinate for the southernmost face or edge of the bounding box. Exclusive minimum: `-90.0`. Exclusive maximum: `90.0`.
    - **`westlimit`** *(number, required)*: A floating point value containing the constant coordinate for the westernmost face or edge of the bounding box. Exclusive minimum: `-180.0`. Exclusive maximum: `180.0`.
    - **`units`** *(string, required)*: A string containing the units applying to the unlabelled numeric values of northlimit, eastlimit, southlimit, and westlimit.
    - **`projection`** *(string)*: A string containing the name of the projection used with any parameters required, such as ellipsoid parameters, datum, standard parallels and meridians, zone, etc. Default: `null`.
- <a id="definitions/BoxSpatialReference"></a>**`BoxSpatialReference`** *(object)*: A class used to represent the metadata associated with the spatial reference of a geographic
feature or raster aggregation expressed as a bounding box.
    - **`type`** *(string)*: A string containing the type of spatial reference. Must be one of: `["box"]`. Must be: `"box"`. Default: `"box"`.
    - **`name`** *(string)*: A string containing a name for the place associated with the spatial reference. Default: `null`.
    - **`northlimit`** *(number, required)*: A floating point value containing the constant coordinate for the northernmost face or edge of the bounding box.
    - **`eastlimit`** *(number, required)*: A floating point value containing the constant coordinate for the easternmost face or edge of the bounding box.
    - **`southlimit`** *(number, required)*: A floating point value containing the constant coordinate for the southernmost face or edge of the bounding box.
    - **`westlimit`** *(number, required)*: A floating point value containing the constant coordinate for the westernmost face or edge of the bounding box.
    - **`units`** *(string, required)*: A string containing the units applying to the unlabelled numeric values of northlimit, eastlimit, southlimit, and westlimit.
    - **`projection`** *(string)*: A string containing the name of the coordinate system used by the spatial reference. Default: `null`.
    - **`projection_string`** *(string, required)*: A string containing an encoding of the coordinate system parameters.
    - **`projection_string_type`** *(string)*: A string containing a description of the type of encoding for the projection string. Default: `null`.
    - **`datum`** *(string)*: A string containing the name of the datum used by the coordinate system. Default: `null`.
    - **`projection_name`** *(string)*: A string containing the name of the coordinate system. Default: `null`.
- <a id="definitions/FieldInformation"></a>**`FieldInformation`** *(object)*: A class used to represent the metadata associated with a field in the attribute table for a geographic
feature aggregation.
    - **`field_name`** *(string, required)*: A string containing the name of the attribute table field.
    - **`field_type`** *(string, required)*: A string containing the data type of the values in the field.
    - **`field_type_code`**: A string value containing a code that indicates the field type. Default: `null`.
        - **Any of**
            - *string*
            - *null*
    - **`field_width`**: An integer value containing the width of the attribute field. Default: `null`.
        - **Any of**
            - *integer*
            - *null*
    - **`field_precision`**: An integer value containing the precision of the attribute field. Default: `null`.
        - **Any of**
            - *integer*
            - *null*
- <a id="definitions/GeometryInformation"></a>**`GeometryInformation`** *(object)*: A class used to represent the metadata associated with the geometry of a geographic feature aggregation.
    - **`feature_count`** *(integer)*: An integer containing the number of features in the geographic feature aggregation. Default: `0`.
    - **`geometry_type`** *(string, required)*: A string containing the type of features in the geographic feature aggregation.
- <a id="definitions/PeriodCoverage"></a>**`PeriodCoverage`** *(object)*: A class used to represent temporal coverage metadata for a resource or aggregation.
    - **`name`** *(string)*: A string containing a name for the time interval. Default: `null`.
    - **`start`** *(string, format: date-time, required)*: A datetime object containing the instant corresponding to the commencement of the time interval.
    - **`end`** *(string, format: date-time, required)*: A datetime object containing the instant corresponding to the termination of the time interval.
- <a id="definitions/PointCoverage"></a>**`PointCoverage`** *(object)*: A class used to represent geographic coverage metadata for a resource or aggregation expressed as a
point location.
    - **`type`** *(string)*: A string containing the type of geographic coverage. Must be one of: `["point"]`. Must be: `"point"`. Default: `"point"`.
    - **`name`** *(string)*: A string containing a name for the place associated with the geographic coverage. Default: `null`.
    - **`east`** *(number, required)*: The coordinate of the point location measured in the east direction. Exclusive minimum: `-180.0`. Exclusive maximum: `180.0`.
    - **`north`** *(number, required)*: The coordinate of the point location measured in the north direction. Exclusive minimum: `-90.0`. Exclusive maximum: `90.0`.
    - **`units`** *(string, required)*: The units applying to the unlabelled numeric values of north and east.
    - **`projection`** *(string, required)*: The name of the projection used with any parameters required, such as ellipsoid parameters, datum, standard parallels and meridians, zone, etc.
- <a id="definitions/PointSpatialReference"></a>**`PointSpatialReference`** *(object)*: A class used to represent the metadata associated with the spatial reference of a geographic
feature or raster aggregation expressed as a point.
    - **`type`** *(string)*: A string containing the type of spatial reference. Must be one of: `["point"]`. Must be: `"point"`. Default: `"point"`.
    - **`name`** *(string)*: A string containing a name for the place associated with the spatial reference. Default: `null`.
    - **`east`** *(number, required)*: The coordinate of the point location measured in the east direction.
    - **`north`** *(number, required)*: The coordinate of the point location measured in the north direction.
    - **`units`** *(string, required)*: The units applying to the unlabelled numeric values of north and east.
    - **`projection`** *(string, required)*: A string containing the name of the coordinate system used by the spatial reference.
    - **`projection_string`** *(string, required)*: A string containing an encoding of the coordinate system parameters.
    - **`projection_string_type`** *(string)*: A string containing a description of the type of encoding for the projection string. Default: `null`.
    - **`projection_name`** *(string)*: A string containing the name of the coordinate system. Default: `null`.
- <a id="definitions/Rights"></a>**`Rights`** *(object)*: A class used to represent the rights statement metadata associated with a resource.
    - **`statement`** *(string, required)*: A string containing the text of the license or rights statement.
    - **`url`** *(string, format: uri, required)*: An object containing the URL pointing to a description of the license or rights statement.
