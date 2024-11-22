import os
import jsonschema2md
import json

from hsmodels.schemas.resource import ResourceMetadata
from hsmodels.schemas.aggregations import (
    FileSetMetadata,
    GeographicRasterMetadata,
    GeographicFeatureMetadata,
    MultidimensionalMetadata,
    ReferencedTimeSeriesMetadata,
    SingleFileMetadata,
    TimeSeriesMetadata,
    ModelInstanceMetadata,
    ModelProgramMetadata,
    CSVFileMetadata
)

aggregation_models = [
    ResourceMetadata,
    FileSetMetadata,
    GeographicRasterMetadata,
    GeographicFeatureMetadata,
    MultidimensionalMetadata,
    ReferencedTimeSeriesMetadata,
    SingleFileMetadata,
    TimeSeriesMetadata,
    ModelInstanceMetadata,
    ModelProgramMetadata,
    CSVFileMetadata
]


def write_md(model):
    sj_rm = model.schema_json(indent=4)
    sj_rm = sj_rm.replace("$defs", "definitions")
    parser = jsonschema2md.Parser()
    parser.tab_size = 4
    md_lines = parser.parse_schema(json.loads(sj_rm))

    filename = model.__name__ + ".md"
    with open(os.path.join(filename), "w") as f:
        f.writelines(md_lines)


for aggr_model in aggregation_models:
    write_md(aggr_model)
