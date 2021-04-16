import uvicorn as uvicorn
from fastapi import FastAPI

from hsclient.hydroshare import HydroShare
from hsmodels.schemas.resource import ResourceMetadata
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/czhub", StaticFiles(directory="czhub"), name="czhub")

hs = HydroShare('sblack', 'j1u2n3o4')


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/resource/{resource_id}/", response_model=ResourceMetadata)
def resource(resource_id: str):
    res = hs.resource(resource_id)
    metadata = res.metadata
    return metadata


@app.post("/resource/{resource_id}/")
def save_resource(resource_id: str, metadata: ResourceMetadata):
    res = hs.resource(resource_id)
    res.save(metadata)


@app.get("/schema/{schema_type}/")
def schema_hydroshare(schema_type: str):
    return ResourceMetadata.schema()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)