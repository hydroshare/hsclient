# HS RDF python client examples

Authentication
```python
from hsclient import HydroShare

hs = HydroShare('username', 'password')
# or
hs = HydroShare()
hs.sign_in()
```
### Resource Creation
access/update metadata

```python
new_resource = hs.create()

new_resource.metadata.title = "Look how easy it is to add a title"
new_resource.metadata.description.abstract = "and it's so easy to add an abstract"
new_resource.metadata.subjects = ['so', 'easy']

new_resource.save()

# or if you want to delete the resource
new_resource.delete()
```
### File Handling
download/upload files
```python
res = hs.resource("84805fd615a04d63b4eada65644a1e20")

# download the resource bag
res.download("bag/download/save/path")

# download single file
file = res.file(name="filename.txt")
res.file_download(file, "file/download/save/path")

# delete file
res.file_delete(file)

# upload one or more files
res.file_upload("file1.txt", "file2.txt")
```
### Aggregations
create/remove aggregations and update metadata

```python
file = res.file(name="file1.txt")

from hsclient.hydroshare import AggregationType

agg = file.aggregate(AggregationType.SingleFileAggregation)

agg.metadata.title = "Adding an aggregation title to an aggregation"
agg.metadata.subject = ['aggregation', 'keywords']
agg.save()

res.aggregation_remove(agg) # remove metadata from files
res.aggregation_delete(agg)  # deletes metadata along with files within aggregation
```
### Analyses
moving file to python performant data structures
```python
agg = res.aggregation(type="TimeSeries")

#dataframe = agg.as_series(res.metadata.)
```
