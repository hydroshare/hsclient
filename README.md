# hsclient
A python client for interacting with HydroShare in an object oriented way. The hsclient Python package can be use to create, modify, and interact with HydroShare resources. It was designed to allow you to write code to do pretty much everything you can do through HydroShare's web user interface.

## Jupyter Notebooks
HydroShare has a resource with example Jupyter notebooks for using hsclient.  Click [here](https://www.hydroshare.org/resource/7561aa12fd824ebb8edbee05af19b910/) then click the blue `Open with...` dropdown at the top of the page and select `Cuahsi Jupyterhub` to launch the notebooks into HydroShare's linked Jupyter Environment. [Click here](https://help.hydroshare.org/apps/CUAHSI-JupyterHub/) for information on how to access the HydroShare linked JupyterHub environment.


## Install the hsclient HydroShare Python Client
The hsclient package is installed already in HydroShare's linked JupyterHub Python environment. However, if you want to use hsclient outside of that Python environment, hsclient won't be installed by default. You'll need to install it before you can work with it. Use the following command to pip install hsclient from the Python Package Index (PyPI). You can also use the package manager for your interactive development environment to do this. 

```bash
pip install hsclient
```

## Getting Started and Documentation

The following are quick examples of how to get started with hsclient. Refer to the Jupyter notebooks above for more extensive examples. [Click here](https://hydroshare.github.io/hsclient/) to access documentation for hsclient.

### Authenticate with HydroShare
Before you start interacting with resources in HydroShare you will need to authenticate.
```python
from hsclient import HydroShare

hs = HydroShare()
hs.sign_in()
```

### Create a New Empty Resource
A "resource" is a container for your content in HydroShare. Think of it as a "working directory" into which you are going to organize the code and/or data you are using and want to share. The following code can be used to create a new, empty resource within which you can create content and metadata.

This code creates a new resource in HydroShare. It also creates an in-memory object representation of that resource in your local environmment that you can then manipulate with further code.
```python
# Create the new, empty resource
new_resource = hs.create()

# Get the HydroShare identifier for the new resource
resIdentifier = new_resource.resource_id
print('The HydroShare Identifier for your new resource is: ' + resIdentifier)

# Construct a hyperlink for the new resource
print('Your new resource is available at: ' +  new_resource.metadata.url)
```

### Creating and Editing Resource Metadata Elements
Editing metadata elements for a resource can be done in an object oriented way. You can specify all of the metadata elements in code, which will set their values in memory in your local environment. Values of metadata elements can be edited, removed, or replaced by setting them to a new value, appending new values (in the case where the metadata element accepts a list), or by removing the value entirely.

When you are ready to save edits to metadata elements from your local environment to the resource in HydroShare, you can call the save() function on your resource and all of the new metadata values you created/edited will be saved to the resource in HydroShare.

### Resource Title and Abstract
The Title and Abstract metadata elements can be specified as text strings. To modify the Title or Abstract after it has been set, just set them to a different value.

```python
# Set the Title for the resource
new_resource.metadata.title = 'Resource for Testing the HS RDF HydroShare Python Client'

# Set the Abstract text for the resource
new_resource.metadata.abstract = (
    'This resource was created as a demonstration of using the HS RDF ' 
    'Python Client for HydroShare. Once you have completed all of the '
    'steps in this notebook, you will have a fully populated HydroShare '
    'Resource.'
)

# Call the save function to save the metadata edits to HydroShare
new_resource.save()

# Print the title just added to the resource
print('Title: ' + new_resource.metadata.title)
print('Abstract: ' + new_resource.metadata.abstract)
```

## Funding and Acknowledgements

This material is based upon work supported by the National Science Foundation (NSF) under awards [1931278](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1931278) and [1931297](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1931297). Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the NSF.

