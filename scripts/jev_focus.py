"""Research-only Jev context/wording ablations; no default parser change."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TypeVar

from tf_jev.decisions import ChoiceQuestion, DecisionRequest, Option
from tf_jev.grounded import GRAMMAR, GroundedParser, _GroundedRun, _json
from tf_jev.ir import PredicateOp
from tf_jev.parser import _Run

T = TypeVar('T')
OPERATORS = {
    PredicateOp.EQ: 'annotation equals the requested literal value(s)',
    PredicateOp.NE: 'annotation does not equal any of the requested literal value(s)',
    PredicateOp.PRESENT: 'annotation exists, regardless of its value',
    PredicateOp.ABSENT: 'annotation is missing on the node',
    PredicateOp.GT: 'integer annotation is greater than the stated integer',
    PredicateOp.LT: 'integer annotation is less than the stated integer',
}


@dataclass(frozen=True)
class FocusedParser(GroundedParser):
    variant: str = 'focused'

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.variant not in ('control', 'focused', 'literal'):
            raise ValueError('unknown research variant')

    def _new_run(self, request: str) -> _Run:
        if self.variant == 'control':
            return _GroundedRun(self, request)
        return _FocusedRun(self, request)


class _FocusedRun(_GroundedRun):
    stage = ''

    def context(self) -> dict[str, str]:
        # Keep precisely the same selected history, request and untrusted-data
        # contract. Choice descriptions still enumerate the FULL admissible domain.
        context = _Run.context(self)
        if self.stage in ('shape', 'verify'):
            context['grammar'] = GRAMMAR
        if self.stage != 'shape':
            context['roles'] = (
                'For containment/exclusion role 0 is the returned parent and role 1 '
                'the child witness. Otherwise roles follow mention order. '
                'A witness constraint does not constrain its parent.'
            )
            context['focus'] = _json(self.focus)
        if self._candidate is not None:
            context['candidate'] = self._candidate
        return context

    def choose(self, name: str, prompt: str, options: list[tuple[T, str]]) -> T:
        self.stage = name
        parser = self.parser
        assert isinstance(parser, FocusedParser)
        if parser.variant == 'literal' and name.endswith('.operator'):
            feature = json.loads(self.state[name.removesuffix('.operator') + '.feature'])
            prompt = (
                f'For node role {self.focus["index"]} of type {self.focus["object_type"]}, '
                f'what comparison does the request require on annotation {feature["name"]}? '
                'Choose the meaning, not the symbol. Presence means an annotation '
                'exists; absence means it is missing, not a sentinel literal.'
            )
            options = [
                (value, f'{description}: {OPERATORS[value]}')
                if isinstance(value, PredicateOp) else (value, description)
                for value, description in options
            ]
        return super().choose(name, prompt, options)


def type_probe(request: DecisionRequest, variant: str) -> DecisionRequest:
    """Ablate a captured predicted type question without adding/removing a type."""
    if variant not in ('control', 'request_only', 'plain', 'reverse'):
        raise ValueError('unknown type probe')
    if len(request.questions) != 1:
        raise ValueError('one type question required')
    name, question = next(iter(request.questions.items()))
    if not name.endswith('.type') or not isinstance(question, ChoiceQuestion):
        raise ValueError('type question required')
    if variant == 'control':
        return request
    context = {k: request.context[k] for k in ('request', 'contract')}
    if variant in ('plain', 'reverse'):
        options = tuple(Option(o.label, json.loads(o.description or '')['name'])
                        for o in question.options)
        if variant == 'reverse':
            options = tuple(reversed(options))
        question = ChoiceQuestion('Which corpus object type is being requested?', options)
    return DecisionRequest(context, {name: question})
