import uvicorn as uvicorn
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse

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
               authorize_url='',
               token_endpoint='')

def _hs(token: str):
    return HydroShare(token=token, client_id=config.get("HYDROSHARE_CLIENT_ID"))

def hs(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return _hs(access_token)

@app.route('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.hydroshare.authorize_redirect(request, redirect_uri)


@app.route('/auth')
async def auth(request: Request):
    try:
        token = await oauth.hydroshare.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    request.session['access_token'] = token['access_token']
    return RedirectResponse(url='/czhub/portal.html')


@app.route('/logout')
async def logout(request: Request):
    request.session.pop('access_token', None)
    return RedirectResponse(url='/czhub/portal.html')

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