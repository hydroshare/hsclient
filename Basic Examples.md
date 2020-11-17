# HS RDF python client examples

Authentication
```python
from hs_rdf.implementations.hydroshare import HydroShare

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
file = next(file for file in res.files if file.name == "filename.txt")
file.download("file/download/save/path")

# delete file
file.delete()

# upload one or more files
hs.upload("file1.txt", "file2.txt")
```
### Aggregations
create/remove aggregations and update metadata
```python
file = next(file for file in res.files if file.name == "file1.txt")

from hs_rdf.implementations.hydroshare import AggregationType

file.aggregate(AggregationType.SingleFileAggregation)

res.refresh()

agg = next(agg for agg in res.aggregations if any(file for file in agg.files if file.name == "file1.txt"))
agg.metadata.title = "Adding an aggregation title to an aggregation"
agg.metadata.subject = ['aggregation', 'keywords']
agg.save()

agg.remove() # remove metadata from files
agg.delete() # deletes metadata along with files within aggregation
```
### Analyses
moving file to python performant data structures
```python
agg = next(agg for agg in res.aggregations if agg.type == "TimeSeries")

dataframe = agg.as_dataframe()
```
