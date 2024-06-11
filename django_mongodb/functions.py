from django.db import NotSupportedError
from django.db.models.expressions import Func
from django.db.models.functions.datetime import Extract
from django.db.models.functions.math import Ceil, Cot, Degrees, Log, Power, Radians, Random, Round
from django.db.models.functions.text import Upper

from .query_utils import process_lhs

MONGO_OPERATORS = {
    Ceil: "ceil",
    Degrees: "radiansToDegrees",
    Power: "pow",
    Radians: "degreesToRadians",
    Random: "rand",
    Upper: "toUpper",
}


def cot(self, compiler, connection):
    lhs_mql = process_lhs(self, compiler, connection)
    return {"$divide": [1, {"$tan": lhs_mql}]}


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
    return {operator: lhs_mql}


def func(self, compiler, connection):
    lhs_mql = process_lhs(self, compiler, connection)
    operator = MONGO_OPERATORS.get(self.__class__, self.function.lower())
    return {f"${operator}": lhs_mql}


def log(self, compiler, connection):
    # This function is usually log(base, num) but on MongoDB it's log(num, base).
    clone = self.copy()
    clone.set_source_expressions(self.get_source_expressions()[::-1])
    return func(clone, compiler, connection)


def round_(self, compiler, connection):
    # Round needs its own function because it's a special case that inherits
    # from Transform but has two arguments.
    return {"$round": [expr.as_mql(compiler, connection) for expr in self.get_source_expressions()]}


def register_functions():
    Cot.as_mql = cot
    Extract.as_mql = extract
    Func.as_mql = func
    Log.as_mql = log
    Round.as_mql = round_
