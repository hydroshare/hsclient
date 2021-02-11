import uvicorn as uvicorn
from fastapi import FastAPI

from hsclient.hydroshare import HydroShare
from hsmodels.schemas.resource import ResourceMetadata

app = FastAPI()
hs = HydroShare('admin', 'default')


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/resource/{resource_id}", response_model=ResourceMetadata, response_model_by_alias=False, response_model_exclude_none=True)
def resource_metadata(resource_id: str):
    res = hs.resource(resource_id)
    return res.metadata


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)