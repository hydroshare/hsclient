import uvicorn as uvicorn
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse

from hsclient.hydroshare import HydroShare
from hsmodels.schemas.resource import ResourceMetadata
from fastapi.staticfiles import StaticFiles
from authlib.integrations.starlette_client import OAuth, OAuthError


app = FastAPI()
app.mount("/czhub", StaticFiles(directory="czhub"), name="czhub")
app.add_middleware(SessionMiddleware, secret_key="!secret")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

config = Config('config/.env')
oauth = OAuth(config)
oauth.register(name='hydroshare',
               authorize_url="https://www.hydroshare.org/o/authorize/",
               token_endpoint="https://www.hydroshare.org/o/token/")
oauth.register(name='orcid',
               authorize_url='https://sandbox.orcid.org/oauth/authorize',
               token_endpoint='https://sandbox.orcid.org/oauth/token',
               client_kwargs={'scope': 'openid'})

db = {}

def _hs(token: str):
    return HydroShare(token=token, client_id=config.get("HYDROSHARE_CLIENT_ID"))

def hs(request: Request):
    orcid = request.session.get("orcid")
    if not orcid:
        raise HTTPException(status_code=401, detail="Unauthorized, not logged into orcid")
    access_token = db[orcid]["hs_access_token"]
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized, HydroShare account not registered")
    return _hs(access_token)

@app.route('/')
def home(request: Request):
    orcid = request.session.get('orcid')
    if orcid:
        if orcid in db:
            return JSONResponse(content={orcid: db[orcid]})
        return JSONResponse(content={"status": f"{orcid} not recognized"})
    return JSONResponse(content={"status": "Not logged in"})

@app.route('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.orcid.authorize_redirect(request, redirect_uri)

@app.route('/authorize/hydroshare')
async def login_hydroshare(request: Request):
    orcid = request.session.get('orcid')
    if not orcid:
        return RedirectResponse("/login")
    redirect_uri = request.url_for('auth_hydroshare')
    return await oauth.hydroshare.authorize_redirect(request, redirect_uri)


@app.route('/auth')
async def auth(request: Request):
    try:
        token = await oauth.orcid.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    if token['orcid'] in db:
        db[token['orcid']]['name'] = token['name']
        db[token['orcid']]['access_token'] = token['access_token']
    else:
        db[token['orcid']] = {"name": token['name'], 'access_token': token['access_token']}
    request.session['orcid'] = token['orcid']
    return RedirectResponse(url='/')

@app.route('/auth/hydroshare')
async def auth_hydroshare(request: Request):
    try:
        token = await oauth.hydroshare.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    orcid = request.session.get('orcid')
    if not orcid:
        raise HTTPException(status_code=400, detail="No logged in with an orcid, cannot authorize hydroshare")
    db[orcid]["hs_access_token"] = token['access_token']
    return RedirectResponse(url='/')



@app.route('/logout')
async def logout(request: Request):
    request.session.pop('orcid', None)
    return RedirectResponse(url='/')

@app.get("/resource/{resource_id}/", response_model=ResourceMetadata)
def resource(request: Request, resource_id: str):
    res = hs(request).resource(resource_id)
    metadata = res.metadata
    return metadata


@app.post("/resource/{resource_id}/")
def save_resource(request: Request, resource_id: str, metadata: ResourceMetadata):
    '''
    Possible interface for saving to a repository:
    To avoid quirks in schema validation, we can provide a sanitize method to take the form json and do anything
    the repository expects
    '''
    res = hs(request).resource(resource_id)
    res.save(metadata)


@app.get("/schema/{schema_type}/")
def schema_hydroshare(schema_type: str):
    return ResourceMetadata.schema()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, ssl_keyfile='config/example.com+5-key.pem', ssl_certfile="config/example.com+5.pem")