# Make RDF metadata easier

The way HydroShare has written RDF
```python
from xml import etree
def get_xml(self):
    RDF_ROOT = etree.Element('{%s}RDF' % self.NAMESPACES['rdf'], nsmap=self.NAMESPACES)
    # create the Description element -this is not exactly a dc element
    rdf_Description = etree.SubElement(RDF_ROOT, '{%s}Description' % self.NAMESPACES['rdf'])
    
    resource_uri = self.identifiers.all().filter(name='hydroShareIdentifier')[0].url
    rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'], resource_uri)
        
    # create the title element
    if self.title:
        dc_title = etree.SubElement(rdf_Description, '{%s}title' % self.NAMESPACES['dc'])
        dc_title.text = self.title.value

    # we're not reading the metadata using this method
```
### Using rdflib
simpler, but still difficult to work with
```python
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, DC, DCTERMS

HSTERMS = Namespace("https://www.hydroshare.org/terms/")

# create
g = Graph()
resource = URIRef("http://www.hydroshare.org/resource/6e83a793ca12497ba1d20993b76e31fd")
g.add((HSTERMS.resource, RDF.type, resource))
g.add((resource, DC.title, Literal("The resource title")))

# update
g.remove((resource, DC.title, None))
g.add((resource, DC.title, Literal("an updated title")))

# read
title = g.value(subject=resource, predicate=DC.title)

# title is an easy one, let's look at the abstract

# create
g = Graph()
resource = URIRef("http://www.hydroshare.org/resource/6e83a793ca12497ba1d20993b76e31fd")
g.add((HSTERMS.resource, RDF.type, resource))
description_node = BNode()
g.add((resource, DC.description, description_node))
g.add((description_node, DCTERMS.abstract, Literal("The abstract is this string")))

# update
description_node = g.value(subject=resource, predicate=DC.description)
g.remove((description_node, DCTERMS.abstract, None))
g.add((description_node, DCTERMS.abstract, Literal("an updated abstract")))

# read
description_node = g.value(subject=resource, predicate=DC.description)
abstract = g.value(subject=description_node, predicate=DCTERMS.abstract)

# write to file
g.serialize("resourcemetadata.xml")

# read from file
g = Graph().parse("resourcemetadata.xml")

```
### rdf-pydantic
put all the rdf bits into a schema
```python
import uuid
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel, RDFIdentifier
from pydantic import Field, AnyUrl
from hs_rdf.namespaces import HSRESOURCE, HSTERMS
from rdflib.namespace import RDF, DC, DCTERMS

def hs_uid():
    return getattr(HSRESOURCE, uuid.uuid4().hex)

class Description(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.Description)

    abstract: str = Field(rdf_predicate=DCTERMS.abstract)

class ResourceMetadata(RDFBaseModel):
    rdf_subject: RDFIdentifier = Field(default_factory=hs_uid)
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.resource, include=True)

    title: str = Field(rdf_predicate=DC.title, default=None)
    description: Description = Field(rdf_predicate=DC.description, default=None)
```
Now use the schema to create/update/read/delete
```python
# new resource
resource = ResourceMetadata()
# update
resource.title = "a resource title"
resource.description.abstract = "an abstract"
# read
title = resource.title
abstract = resource.description.abstract
# write
resource.title = "a resource title"
resource.description.abstract = "an abstract"
# to file
resource.serialize("resourcemetadata.xml")
# to string
resource.rdf_string()

# read from file
resource = ResourceMetadata.parse_file("resourcemetadata.xml")
```
### Example HydroShare Django Models
rdf-pydantic models translate easily from our existing Django models.  Compare the models below with the rdf-pydantic schemas above
```python
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from hs_core.models import AbstractMetaDataElement

class Description(AbstractMetaDataElement):
    """Define Description metadata element model."""

    term = 'Description'
    abstract = models.TextField()

class Title(AbstractMetaDataElement):
    """Define Title metadata element model."""

    term = 'Title'
    value = models.CharField(max_length=300)

class CoreMetaData(models.Model):
    """Define CoreMetaData model."""

    XML_HEADER = '''<?xml version="1.0"?>
<!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"
"http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">'''

    NAMESPACES = {'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  'rdfs1': "http://www.w3.org/2000/01/rdf-schema#",
                  'dc': "http://purl.org/dc/elements/1.1/",
                  'dcterms': "http://purl.org/dc/terms/",
                  'hsterms': "https://www.hydroshare.org/terms/"}

    id = models.AutoField(primary_key=True)

    _description = GenericRelation(Description)    # resource abstract
    _title = GenericRelation(Title)
```

### Decouple metadata models from Django
By translating our metadata models from Django to rdf-pydantic, we are no longer tied to django and a relational database.  Working with the rdf-pydantic schemas will be a very similar experience to django models, but without django.

### Consolidate Validation
Currently, model validation is spread across django models, forms, functions, and even the frontend.  All validation and documentation may be consolidated to the pydantic models.

### DSAW HydroShare python client
This project is translating the schemas for us to provide an object oriented experience of interacting with HydroShare metadata

```python
from hs_rdf.implementations.hydroshare import HydroShare

# username/password can be passed to Hydroshare constructor
hs = HydroShare()
# or you can call sign_in() for prompts
hs.sign_in()

# retrieves a resource by id
resource = hs.resource('09041bbe8015485db414a4d41b3575db')

# access metadata object and title attribute (using rdf-pydantic schemas)
print(resource.metadata.title)
resource.metadata.title = "updated resource title"
resource.save()
```

### Schema driven API
pydantic and rdflib give us flexibility to serve and receive a variety of input types without writing new code.

##### rdflib supports most (all?) rdf serializations
* rdf/xml
* json-ld
* turtle
* etc...

##### pydantic supports
* json-schema
* json
* and more...

##### pydantic harnessed in FastAPI
* OpenAPI (Swagger) 
* schema-driven api
* Store data however we want (not tied to a relational database)

### User declared schemas
Model Program/Instance allows users to declare a JSON Schema.  Those JSON schemas can be programmatically translated to pydantic models and harnessed in the same way our native schemas are.

### Simplify HydroShare 
The core idea of a hydroshare resource is metadata attached to a set of files.  HydroShare currently implements this idea in several different ways, Resource types (Composite, Model Program/Instance, etc), Collection, Aggregations, Model Program JSON schema.  These multiple approaches requires quite a bit of development and support to add new metadata schemas.

We can simplify our codebase by creating a schema driven api.  The structure, validation and documentation of the schema exists within the schema and is used by the schema driven api.  Users could also provide custom schemas by submitting a JSON schema that is then translated the pydantic model to be used in the same way as our native schemas (Resource, aggregation types)

