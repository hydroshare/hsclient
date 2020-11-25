from pydantic import BaseModel



class BaseMetadata(BaseModel):

    class Config:
        validate_assignment = True

    def _rdf_model_instance(self):
        d = self.dict()
        rdf_model = self._rdf_model_class(**d)
        return rdf_model

    def rdf_string(self, rdf_format='pretty-xml'):
        from hs_rdf.schemas import rdf_string
        return rdf_string(self._rdf_model_instance(), rdf_format)

    def rdf_graph(self):
        from hs_rdf.schemas import rdf
        return rdf(self._rdf_model_instance())

    @classmethod
    def parse_file(cls, file, file_format='xml', subject=None):
        from hs_rdf.schemas import parse_file
        return parse_file(cls._rdf_model_class, file, file_format, subject)

    @classmethod
    def parse(cls, metadata_graph, subject=None):
        rdf_metadata = cls._rdf_model_class.parse(metadata_graph, subject)
        instance = cls(**rdf_metadata.dict())
        return instance
