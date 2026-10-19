"""Conservative English/BHSA single-atom baseline; no benchmark/gold imports."""

from __future__ import annotations

import re
from dataclasses import dataclass

from tf_jev.compiler import CompileError, compile_query
from tf_jev.ir import Atom, Predicate, PredicateOp, Query
from tf_jev.parser import ParseResult, ParseStatus
from tf_jev.schema import CorpusSchema, SchemaError

# Explicit BHSA annotation adapter, independently validated against the schema.
_POS = {
    "verbs": "verb",
    "nouns": "subs",
    "proper nouns": "nmpr",
    "adjectives": "adjv",
    "adverbs": "advb",
    "prepositions": "prep",
    "conjunctions": "conj",
    "articles": "art",
    "personal pronouns": "prps",
    "negative particles": "nega",
}
_GENDER = {"feminine": "f", "masculine": "m"}
_NUMBER = {"singular": "sg", "plural": "pl", "dual": "du"}
_POS_PATTERN = "|".join(map(re.escape, _POS))


@dataclass(frozen=True)
class BHSARuleParser:
    schema: CorpusSchema

    def parse(self, request: str) -> ParseResult:
        predicates: list[Predicate] = []
        if type(request) is not str or self.schema.coverage.mode != "full":
            return self._result()
        # Full matches deliberately refuse extra scope/aggregation/relations.
        pos = re.fullmatch(r"Return all words annotated as (" + _POS_PATTERN + r")\.", request)
        morph = re.fullmatch(
            r"Return (" + _POS_PATTERN + r") annotated as (feminine|masculine) and "
            r"(singular|plural|dual)\.",
            request,
        )
        literal = re.fullmatch(
            r"""Return words whose lex annotation is exactly (['"])([^\r\n]+)\1\.""",
            request,
        )
        if pos:
            predicates.append(Predicate("sp", PredicateOp.EQ, (_POS[pos[1]],)))
        elif morph:
            predicates.extend(
                (
                    Predicate("sp", PredicateOp.EQ, (_POS[morph[1]],)),
                    Predicate("gn", PredicateOp.EQ, (_GENDER[morph[2]],)),
                    Predicate("nu", PredicateOp.EQ, (_NUMBER[morph[3]],)),
                )
            )
        elif literal and literal[1] not in literal[2]:
            predicates.append(Predicate("lex", PredicateOp.EQ, (literal[2],)))
        else:
            return self._result()
        ir = Query((Atom("word", tuple(predicates)),))
        try:
            compiled = compile_query(ir, self.schema)
        except (CompileError, SchemaError, ValueError):
            return self._result()
        return ParseResult(
            ParseStatus.SUPPORTED,
            "rule_match",
            ir,
            compiled,
            (0,),
            1.0,
            (),
            self.schema.identity.key,
        )

    def _result(self) -> ParseResult:
        return ParseResult(
            ParseStatus.UNSUPPORTED,
            "rule_no_match",
            None,
            None,
            (),
            0.0,
            (),
            self.schema.identity.key,
        )
