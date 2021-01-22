# HS RDF python client examples


Installation
```bash
python -m pip install git+https://github.com/sblack-usu/hs_rdf.git
```

Upgrading
```bash
python -m pip install --upgrade --force-reinstall git+https://github.com/sblack-usu/hs_rdf.git
```

Authentication
```python
from hs_rdf.hydroshare import HydroShare
username = "username"
password = "password"
hs = HydroShare(username, password, 'dev-hs-1.cuahsi.org', 'https', 443)
```
### Resource Creation
access/update metadata

```python
new_resource = hs.create()
print(new_resource.metadata.url.path)

new_resource.metadata.title = "Look how easy it is to add a title"
new_resource.metadata.description.abstract = "and it's so easy to add an abstract"
new_resource.metadata.subjects = ['so', 'easy']

new_resource.save()

# or if you want to delete the resource
new_resource.delete()
```
### File Handling
download/upload/delete files
```python
res = hs.resource("1248abc1afc6454199e65c8f642b99a0")

# download the resource bag
res.download("downloads")

# download single file
file = res.file(name="readme.txt")
res.file_download(file, "downloads")

# delete file
res.file_delete(file)

# upload one or more files
res.file_upload("downloads/readme.txt")
```
### Aggregations
create/remove aggregations and update metadata (not complete)

```python
file = res.file(name="readme.txt")

from hs_rdf.hydroshare import AggregationType

agg = file.aggregate(AggregationType.SingleFileAggregation)

agg.metadata.title = "Adding an aggregation title to an aggregation"
agg.metadata.subjects = ['aggregation', 'keywords']
agg.save()

res.aggregation_remove(agg)  # remove metadata from files
res.aggregation_delete(agg)  # deletes metadata along with files within aggregation
```

