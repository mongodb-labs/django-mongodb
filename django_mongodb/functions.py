from django.db import NotSupportedError
from django.db.models.expressions import Col
from django.db.models.functions.datetime import Extract

from .query_utils import process_lhs


def extract(self, compiler, connection):
    lhs_mql = process_lhs(self, compiler, connection)
    if self.lookup_name == "week":
        operator = "$week"
    elif self.lookup_name == "month":
        operator = "$month"
    elif self.lookup_name == "year":
        operator = "$year"
    else:
        raise NotSupportedError("%s is not supported." % self.__class__.__name__)
    if isinstance(self.lhs, Col):
        lhs_mql = f"${lhs_mql}"
    return {operator: lhs_mql}


def register_functions():
    Extract.as_mql = extract
