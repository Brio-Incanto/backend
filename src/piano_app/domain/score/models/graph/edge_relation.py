from enum import StrEnum


class EdgeRelation(StrEnum):
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    STARTS_AT = "starts_at"
    ENDS_AT = "ends_at"
