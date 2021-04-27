import time

import uvicorn as uvicorn
from irods.session import iRODSSession
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

from hsmodels.schemas.resource import ResourceMetadata


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")

#session = iRODSSession(host='hydrotest.renci.org', port=1247, user='betaDataProxy', password='meipaithoongeiphuquei4ooKuengeij', zone='hydrotestZone')
session = iRODSSession(host='dev-irods-1.cuahsi.org', port=1247, user='cuahsi1DataProxy', password='icaxahreiFah9oojaiz7Cieg7nah3jah', zone='hydroshareZone')
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

def get_res(resource_id):
    start_time = time.time()
    resmap = session.data_objects.get(f"/hydrotestZone/home/betaDataProxy/{resource_id}/data/resourcemetadata.xml")
    with resmap.open('r') as f:
        #return load_rdf(f.read())
        read = f.read()
    process_time = time.time() - start_time
    print(process_time)

@app.get("/resource/{resource_id}/")
def resource(resource_id: str):
    resmap = session.data_objects.get(f"/hydrotestZone/home/betaDataProxy/{resource_id}/data/resourcemetadata.xml")
    with resmap.open('r') as f:
        #return load_rdf(f.read())
        return f.read()

@app.get("/empty/")
def empty_response():
    return ""


@app.post("/resource/{resource_id}/")
def save_resource(request: Request, resource_id: str, metadata: ResourceMetadata):
    '''
    Possible interface for saving to a repository:
    To avoid quirks in schema validation, we can provide a sanitize method to take the form json and do anything
    the repository expects
    '''
    #res = hs(request).resource(resource_id)
    #res.save(metadata)


@app.get("/schema/{schema_type}/")
def schema_hydroshare(schema_type: str):
    return ResourceMetadata.schema()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, ssl_keyfile='config/example.com+5-key.pem', ssl_certfile="config/example.com+5.pem")