from enum import StrEnum


class EdgeRelation(StrEnum):
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    PRECEDES = "precedes"
    STARTS_AT = "starts_at"
    ENDS_AT = "ends_at"
