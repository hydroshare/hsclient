---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.10.0
  kernelspec:
    display_name: PyCharm (hsclient)
    language: python
    name: pycharm-ef6cf96c
---

<!-- #region id="HHsuQMMJyms4" -->
# HS RDF HydroShare Python Client Resource Aggregation Operation Examples 


---


The following code snippets show examples for how to use the HS RDF HydroShare Python Client to manipulate aggregations of known content types in HydroShare. HydroShare's content type aggregations include individual file, fileset, time series, geographic feature, geographic raster, and multidimensional NetCDF.
<!-- #endregion -->

<!-- #region id="b_Tj5gJx0fRj" -->
## Install the HS RDF Python Client

The HS RDF Python Client for HydroShare won't be installed by default, so it has to be installed first before you can work with it. Use the following command to install the Python Client from the GitHub repository. Eventually we will distribute this package via the Python Package Index (PyPi) so that it can be installed via pip from PyPi.
<!-- #endregion -->

```python id="hzriLgMl0oJ2"
!pip install git+https://github.com/hydroshare/hsclient.git
```

<!-- #region id="CZNOazcn9-23" -->
## Authenticating with HydroShare

Before you start interacting with resources in HydroShare you will need to authenticate.
<!-- #endregion -->

```python id="3njsiY73m7_V"
from hsclient import HydroShare

hs = HydroShare()
hs.sign_in()
```

<!-- #region id="TH3UUihSojIb" -->
## Create a New Empty Resource

A "resource" is a container for your content in HydroShare. Think of it as a "working directory" into which you are going to organize the code and/or data you are using and want to share. The following code can be used to create a new, empty resource within which you can create content and metadata.

This code creates a new resource in HydroShare. It also creates an in-memory object representation of that resource in your local environmment that you can then manipulate with further code.
<!-- #endregion -->

```python id="W9azvJ_Co87w"
# Create the new, empty resource
new_resource = hs.create()

# Get the HydroShare identifier for the new resource
resIdentifier = new_resource.resource_id
print('The HydroShare Identifier for your new resource is: ' + resIdentifier)

# Construct a hyperlink for the new resource
print('Your new resource is available at: ' +  new_resource.metadata.url)
```

<!-- #region id="rcrEJDQkOtI8" -->
## Resource Aggregation Handling

HydroShare allows you to create and manage aggregations of content files within resources that have specific types and associated metadata. These known content types include:

* Time series
* Geographic feature
* Geographic raster
* Multidimensional NetCDF
* Single file
* File set

The general process for creating an aggregation within a resource requires adding files to the resource and then applying the appropriate aggregation type. For some of the aggregation types, some of the aggregation metadata fields will be automatically extracted from the files you upload. You can then set the values of the other aggregation-level metadata elements. 
<!-- #endregion -->

<!-- #region id="7yUSEF_tOySg" -->
## Create a Single File Aggregation

A single file aggregation in a HydroShare is any individual file to which you want to add extra metadata. 
<!-- #endregion -->

```python id="sCvGL4g-PGXS"
# Import the aggregation types
from hsmodels.schemas.enums import AggregationType

# Upload a single content file to the resource. This is a generic sample comma separated 
# values (CSV) data file with some tabular data
new_resource.file_upload('Example_Files/Data_File1.csv')

# Specify the file you want to add the aggregation to
file = new_resource.file(path="Data_File1.csv")

# Create a single file aggregation on the file and refresh the resource
agg = new_resource.file_aggregate(file, AggregationType.SingleFileAggregation)

# Print the title for the aggregation that was added to the resource
print('The following aggregation was added to the resource: ' + agg.metadata.title)
print('Aggregation type: ' + agg.metadata.type)
```

### Add Metadata to the Aggregation

Once you have created an aggregation, you can edit and add metadata elements. For a single file aggregation, you can add a title, subject keywords, extended metadata as key-value pairs, and spatial and temporal coverage. 

All of the metadata edits are stored locally until you call the `save()` function on the aggregation to write the edits you have made to HydroShare.


#### Title and Keywords

The title of an aggregation is a string. Subject keywords are handled as a list of strings.

```python
# Set the title and subject keywords for the aggregation
agg.metadata.title = "A CSV Data File Single File Aggregation"
agg.metadata.subjects = ['CSV','Aggregation', 'Single File','Data']

# Print the title and keywords for the aggregation
print('Aggregation Title: ' + agg.metadata.title)
print('Aggregation Keywords: ' + ', '.join(agg.metadata.subjects))

# Save the aggregation to write all of the metadata to HydroShare
agg.save()
```

#### Extended Metadata Elements

Extended metadata elements for an aggregation are handled using a Python dictionary. You can add new elements using key-value pairs.

```python
# Add an extended metadata element to the aggregation as a key-value pair 
agg.metadata.additional_metadata['New Element Key'] = 'Text value of new element.'

# Remove an individual key-value pair from the aggregation using its key
del agg.metadata.additional_metadata['New Element Key']

# Or, you can clear out all of the extended metadata elements that might exist
agg.metadata.additional_metadata.clear()

# Add multiple key-value pairs to the aggregation at once using a Python dictionary
agg.metadata.additional_metadata = {
    'Observed Variable': 'Water use',
    'Site Location': 'Valley View Tower Dormatory on Utah State University\'s Campus in Logan, UT'
}

# Print the extended metadata elements
print('The extended metadata elements for the aggregation include:')
for key, value in agg.metadata.additional_metadata.items():
    print (key + ':', value)
    
# Save the aggregation to write all of the metadata to HydroShare
agg.save()
```

#### Spatial and Temporal Coverage

Spatial and temporal coverage for an aggregation are handled in the same way they are handled for resource level metadata. Initially the spatial and temporal coverage for an aggregation are empty. To set them, you have to create a coverage object of the right type and set the spatial or temporal coverage to that object.

```python
# Import the required metadata classes for coverage objects
from hsmodels.schemas.fields import BoxCoverage, PointCoverage, PeriodCoverage
from datetime import datetime

# Set the spatial coverage of the aggregation to a BoxCoverage object
agg.metadata.spatial_coverage = BoxCoverage(name='Logan, Utah',
                                            northlimit=41.7910,
                                            eastlimit=-111.7664,
                                            southlimit=41.6732,
                                            westlimit=-111.9079,
                                            projection='WGS 84 EPSG:4326',
                                            type='box',
                                            units='Decimal degrees')

# You can remove the spatial coverage element by setting it to None
agg.metadata.spatial_coverage = None

# If you want to set the spatial coverage to a PointCoverage instead
agg.metadata.spatial_coverage = PointCoverage(name='Logan, Utah',
                                              north=41.7371,
                                              east=-111.8351,
                                              projection='WGS 84 EPSG:4326',
                                              type='point',
                                              units='Decimal degrees')

# Create a beginning and ending date for a time period
beginDate = datetime.strptime('2020-12-01T00:00:00Z', '%Y-%m-%dT%H:%M:%S%fZ')
endDate = datetime.strptime('2020-12-31T00:00:00Z', '%Y-%m-%dT%H:%M:%S%fZ')

# Set the temporal coverage of the aggregation to a PeriodCoverage object
agg.metadata.period_coverage = PeriodCoverage(start=beginDate, end=endDate)

# Print the temporal coverage information
print('Temporal Coverage')
print(agg.metadata.period_coverage)

# Print the spatial coverage information
print('\nSpatial Coverage')
print(agg.metadata.spatial_coverage)

# Save the aggregation to write all of the metadata to HydroShare
agg.save()
```

## Creating Other Aggregation Types


### Geographic Feature Aggregation

Geographic feature aggregations are created in HydroShare from the set of files that make up an ESRI Shapefile. You need to upload the shapefile and then HydroShare will automatically set the aggregation on the set of files you upload. You can then retrieve the aggregation using its title or by searching for one of the files it contains.

```python
# Create a list of the files that make up the shapefile to be uploaded 
file_list = ['Example_Files/watersheds.cpg', 'Example_Files/watersheds.dbf', 
             'Example_Files/watersheds.prj', 'Example_Files/watersheds.sbn',
             'Example_Files/watersheds.sbx', 'Example_Files/watersheds.shp', 
             'Example_Files/watersheds.shx', 'Example_Files/watersheds.shp.xml']

# Upload the files to the resource all at the same time
new_resource.file_upload(*file_list)

print('Files uploaded!')
```

If you upload all of the files of a shapefile together as shown above, HydroShare automatically recognizes the files as a shapefile and auto-aggregates the files into a geographic feature aggregation for you. So, you then just need to get the aggregation that was created if you want to further operate on it - e.g., to modify the aggregation-level metadata.

Metadata for a geographic feature aggregation includes a title, subject keywords, extended key-value pairs, temporal coverage, spatial coverage, geometry information, spatial reference, and field information. When HydroShare creates the aggregation on the shapefile, the spatial coverage, geometry information, spatial reference, and attribute field information metadata will be automatically set for you. You can then set all of the other metadata elements as shown above for the single file aggregation if you need to.

```python
# Get the aggregation that was just created

# You can get the aggregation by searching for a file that is inside of it
agg = new_resource.aggregation(file__name="watersheds.shp")

# Or, you can get the aggregation by searching for its title, which is initially
# set to the name of the shapefile
agg = new_resource.aggregation(title="watersheds")

# Print the title for the aggregation that was added to the resource
print('The following aggregation was added to the resource: ' + agg.metadata.title)
print('Aggregation type: ' + agg.metadata.type)
```

### Geographic Raster Aggregation

Geographic raster aggregations are created in HydroShare from one or more raster data files that make up a raster dataset. HydroShare uses GeoTiff files for raster datasets. Like the geographic feature aggregation, when you upload all of the files for a geographic raster dataset (all .tif and a .vrt file) at once, HydroShare will automatically create the aggregation for you. You can then get the aggregation and set the other metadata elements as shown above for the single file aggregation.

HydroShare initially sets the title of the geographic raster aggregation to the first .tif file that appears in the .vrt file. The spatial coverage, spatial reference, and cell information are set automatically based on information extracted from the dataset. 

```python
# Upload the files making up the raster dataset to the resource
file_list = ['Example_Files/logan1.tif', 'Example_Files/logan2.tif', 'Example_Files/logan.vrt']
new_resource.file_upload(*file_list)

# Get the aggregation that was just created - initially the title will be "logan1"
# based on the name of the first .tif file that appears in the .vrt file
agg = new_resource.aggregation(title="logan1")

# Print the title for the aggregation that was added to the resource
print('The following aggregation was added to the resource: ' + agg.metadata.title)
print('Aggregation type: ' + agg.metadata.type)
```

### Multidimensional NetCDF Aggregation

Multidimensional aggregations are created in HydroShare from a NetCDF file. Like the other aggregation types, you can upload the NetCDF file and HydroShare will automatically create the aggregation for you. HydroShare also automatically extracts metadata from the NetCDF file to populate the aggregation metadata. Some of this metadata may get propagated to the resource level if you haven't set things like the title and keywords. You can then get the aggregation and set the other metadata elements as shown above for the single file aggregation.

```python
# Upload the NetCDF file to the resource
new_resource.file_upload('Example_Files/SWE_time.nc')

# Get the aggregation by searching for the NetCDF file that is inside of it
agg = new_resource.aggregation(file__name="SWE_time.nc")

# Print the title for the aggregation that was added to the resource
print('The following aggregation was added to the resource: ' + agg.metadata.title)
print('Aggregation type: ' + agg.metadata.type)
```

### Time Series Aggregation

Time series aggregations are created in HydroShare from an ODM2 SQLite database file. The ODM2 SQLite database contain one or more time series 

```python
# Upload the SQLite file to the resource
new_resource.file_upload('Example_Files/ODM2.sqlite')

# Get the aggregation by searching for the SQLite file that is inside of it
agg = new_resource.aggregation(file__name="ODM2.sqlite")

# Print the title for the aggregation that was added to the resource
print('The following aggregation was added to the resource: ' + agg.metadata.title)
print('Aggregation type: ' + agg.metadata.type)
```

### File Set Aggregation

A file set aggregation is any folder within a resource to which you want to add metadata. If you want to create a file set aggregation, you first have to create a folder, then upload files to it. After that, you can set the aggregation on the folder.

```python
# Create a new folder for the file set aggregation
new_resource.folder_create('Fileset_Aggregation')

# Add some files to the folder
new_resource.file_upload('Example_Files/Data_File1.csv', 'Example_Files/Data_File2.csv',
                    destination_path='Fileset_Aggregation')

# TODO: How to set a fileset aggregation on a folder containing files?
```

## Get Aggregation Properties

Each aggregation in a resource has metadata properties associated with it. You can query/retrieve those properties for display. The following shows an example for the time series aggregation that was created above.

```python
# Get the time series aggregation that was created above
agg = new_resource.aggregation(type="TimeSeries")

# Print the metadata associated with the aggregation
print('Aggregation Title: ' + agg.metadata.title)
print('Aggregation Type: ' + agg.metadata.type)
print('Aggregation Keywords: ' + ', '.join(agg.metadata.subjects))
print('Aggregation Temporal Coverage: ' + str(agg.metadata.period_coverage))
print('Aggregation Spatial Coverage: ' + str(agg.metadata.spatial_coverage))

# Print the list of files in the aggregation
file_list = agg.files()
print('List of files contained within the aggregation:')
print(*file_list, sep='\n')
```

## Searching for Aggregations within a Resource

If you need to find/get one or more aggregations within a resource so you can download or remove it from the resource, there are several filters available that allow you to return a list of aggregations that meet your search criteria.

```python
# Get the list of all aggregations in the resource
aggregations = new_resource.aggregations()

# Get a list of all aggregations of a particular type
aggregations = new_resource.aggregations(type="TimeSeries")
 
# Get a list of aggregations with extended metadata searching by key
aggregations = new_resource.aggregations(additional_metadata__key="Observed Variable")
 
# Get a list of aggregations with extended metadata searching by value
aggregations = new_resource.aggregations(additional_metadata__value="Water Use")
 
# Get a list of aggregations with a subject keyword searching by value
aggregations = new_resource.aggregations(subjects__contains="Temperature")
 
# Get a list of aggregations searching by title (or any metadata attribute)
aggregations = new_resource.aggregations(title="watersheds")
 
# Get a list of aggregations searching by a nested metadata attribute (__)
aggregations = new_resource.aggregations(period_coverage__name="period_coverage name")
 
# Get a list of aggregations by combining field searching, filtered with “AND”
aggrregations = new_resource.aggregations(period_coverage__name="period_coverage name", title="watersheds")
```

You can also search for individual aggregations within a resource.

```python
# Search for an aggregation of type time series
aggregation = new_resource.aggregation(type="TimeSeries")

# Search for an aggregation with a specific title
aggregation = new_resource.aggregation(title="watersheds")

# Search for an aggregation that contains a particular file name
aggregation = new_resource.aggregation(file__name="ODM2.sqlite")
```

<!-- #region id="pA-hHbeDKJHk" -->
## Downloading an Aggregation

When working with a resource, you may want to download one of the aggregations contained within the resource. If you want to download it to a particular location on your disk, you can pass a path to the location where you want the aggregation to be saved to the `download()` function as a string. Aggregations are downloaded as a zipped file containing the aggregation content and metadata files.
<!-- #endregion -->

```python id="n1FGhvLfJ6Gz"
# Get the geographic feature aggregation that was created above
agg = new_resource.aggregation(title="watersheds")

# Download the aggregation
new_resource.aggregation_download(agg)
```

<!-- #region id="vrLaW5dXI6x5" -->
Clean up the zippled aggregation file that was just downloaded.
<!-- #endregion -->

```python id="8daPuEdhI7hV"
!rm 'watersheds.shp.zip'
```

<!-- #region id="5rqEkMYoQGmB" -->
## Remove and Delete an Aggregation

You may wish to remove an aggregation from a resource. There are two functions you can use to do this. The difference between the two is whether the aggregation's content files are preserved in the resource or deleted. To remove the aggregation-specific metadata and associations while maintaining the content files, call the `remove()` function on the aggregation.
<!-- #endregion -->

```python id="gwZmuLW-FLcZ"
# Get the geographic raster aggregation that was created above
agg = new_resource.aggregation(title="logan1")

# Remove the aggregation and delete its metadata, but leave the file(s)
new_resource.aggregation_remove(agg)
```

<!-- #region id="LLjrAE6CHjJm" -->
If you want to delete the aggregation, including its metadata and the associated content files, you can call the `delete()` function on the aggregation. Once you have called the `remove()` function on an aggregation, the `delete()` function will no longer work and you will have to delete the files individually.
<!-- #endregion -->

```python id="1pVadpiFQSRo"
# Get the multidimensional NetCDF aggregation that was created above
agg = new_resource.aggregation(type="NetCDF")

# Delete the aggregation and metadata along with files within aggregation
new_resource.aggregation_delete(agg)
```

```python

```
