"""Diagnostic observation must not alter the parser or disclose request data."""
from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.diagnose_abstention import TraceBackend, summarize
from tests.conformance.tf_harness import run_template
from tests.test_parser import ChoosingBackend, choices
from tf_jev.decisions import (
    BackendError, Capabilities, ChoiceDecision, ChoiceQuestion, DecisionBatch,
    DecisionRequest, Option, Receipt,
)
from tf_jev.parser import SemanticParser
from tf_jev.schema import extract_schema


def test_trace_is_transparent_and_native_results_unchanged(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    plain = SemanticParser(schema, ChoosingBackend(choices())).parse('Return verbs.')
    trace = TraceBackend(ChoosingBackend(choices()))
    observed = SemanticParser(schema, trace).parse('Return verbs.')
    assert observed == plain
    assert observed.query and run_template(tiny_api, observed.query).results == ((3,), (6,), (8,))
    assert len(trace.calls) == len(observed.evidence) == 8
    assert all(c['input_tokens'] == 10 for c in trace.calls)
    assert trace.calls[0]['questions'][0]['probabilities'] == pytest.approx([.98,.005,.005,.005,.005])
    assert trace.calls[0]['questions'][0]['selected_index'] == 0
    text = json.dumps(trace.calls)
    assert 'Return verbs' not in text and 'word' not in text and 'verb' not in text
    assert summarize(observed, trace.calls)['stopping_question'] is None


@pytest.mark.parametrize('stage', ['shape', 'atom0.type', 'atom0.pred0.feature'])
def test_low_confidence_stop_identifies_exact_stage(tiny_api: Any, stage: str) -> None:
    trace = TraceBackend(ChoosingBackend(choices(), weak=stage))
    result = SemanticParser(extract_schema(tiny_api), trace).parse('Return verbs.')
    report = summarize(result, trace.calls)
    assert report['stopping_question'] == stage
    assert report['last_observed_question'] == stage
    assert report['calls'][-1]['questions'][0]['top_probability'] == .6
    assert report['calls'][-1]['questions'][0]['margin'] < .8


def test_failed_attempt_does_not_leak_exception_or_look_free(tiny_api: Any) -> None:
    class Broken:
        capabilities = Capabilities()
        def decide(self, request: Any) -> Any:
            raise BackendError('secret_private_body')
    trace = TraceBackend(Broken())
    result = SemanticParser(extract_schema(tiny_api), trace).parse('secret user request')
    assert len(trace.calls) == 1
    row = trace.calls[0]
    assert row['error_kind'] == 'other'
    assert row['input_tokens'] is None and row['output_tokens'] is None
    assert row['questions'] == []
    assert 'secret' not in json.dumps(summarize(result, trace.calls))


def test_batch_usage_once_and_no_raw_labels_names_or_descriptions() -> None:
    class Backend:
        capabilities = Capabilities()
        def decide(self, request: DecisionRequest) -> DecisionBatch:
            return DecisionBatch({name: ChoiceDecision('private_label', {'private_label':1.})
                                  for name in request.questions}, Receipt('fake','fake',0.,13,7))
    request = DecisionRequest({'request':'private_request'}, {
        name: ChoiceQuestion('private_prompt', (Option('private_label','private_description'),))
        for name in ('private_question', 'probe0')})
    trace = TraceBackend(Backend())
    result = trace.decide(request)
    assert result.receipt.input_tokens == 13
    assert len(trace.calls) == 1 and trace.calls[0]['input_tokens'] == 13
    assert len(trace.calls[0]['questions']) == 2
    assert trace.calls[0]['questions'][0]['question'] == 'redacted'
    assert 'private' not in json.dumps(trace.calls)


def test_malformed_backend_distribution_is_not_exported(tiny_api: Any) -> None:
    class Forged:
        capabilities = Capabilities()
        def decide(self, request: Any) -> DecisionBatch:
            return DecisionBatch({'shape': ChoiceDecision('secret', {'secret':1.})},
                                 Receipt('fake','fake',0.,10,2))
    trace = TraceBackend(Forged())
    result = SemanticParser(extract_schema(tiny_api), trace).parse('Return verbs.')
    assert result.status.value == 'error'
    assert trace.calls[0]['error_kind'] == 'contract'
    assert trace.calls[0]['questions'] == []
    assert 'secret' not in json.dumps(trace.calls)
