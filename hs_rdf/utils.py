


def to_coverage_dict(value):
    value_dict = {}
    for key_value in value.split("; "):
        k, v = key_value.split("=")
        value_dict[k] = v
    return value_dict