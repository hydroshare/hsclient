from hs_rdf.implementations.hydroshare import HydroShare

hs = HydroShare()
hs.sign_in()
resource = hs.resource('09041bbe8015485db414a4d41b3575db')
print(resource.metadata.title)

from pathlib import Path
for f in resource.files:
    Path("temp/" + f.relative_folder).mkdir(parents=True, exist_ok=True)
    f.download("temp/" + f.relative_path)

for agg in resource.aggregations:
    print(agg.metadata.title)
    for f in agg.files:
        Path("temp/" + f.relative_folder).mkdir(parents=True, exist_ok=True)
        f.download("temp/" + f.relative_path)


