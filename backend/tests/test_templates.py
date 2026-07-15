import pytest

from app.execution.interpreter import FlowchartInterpreter
from app.templates.definitions import TEMPLATE_REGISTRY
from app.templates.pipeline import load_template_flowchart


def test_template_ids_are_unique():
    ids = [t.id for t in TEMPLATE_REGISTRY]
    assert len(ids) == len(set(ids))


def test_every_template_covers_a_category_from_the_spec():
    categories = {t.category for t in TEMPLATE_REGISTRY}
    expected = {
        "DSA Basics", "Sorting Algorithms", "Searching Algorithms",
        "Operating Systems", "Networking", "Compiler Design", "Database",
    }
    assert expected <= categories


@pytest.mark.parametrize("template", TEMPLATE_REGISTRY, ids=[t.id for t in TEMPLATE_REGISTRY])
def test_every_template_lays_out_with_start_and_end(template):
    _, nodes, edges, warnings = load_template_flowchart(template.id)
    types = [n.type for n in nodes]
    assert "start" in types
    assert "end" in types
    assert len(nodes) >= 2
    assert len(edges) >= 1


def test_unknown_template_id_raises():
    with pytest.raises(ValueError):
        load_template_flowchart("does_not_exist")


def _run(template_id: str, input_values: list[str]):
    _, nodes, edges, _ = load_template_flowchart(template_id)
    return FlowchartInterpreter(nodes, edges, input_values=input_values).run()


def test_factorial_template_computes_correctly():
    result = _run("factorial", ["5"])
    assert result.status == "completed"
    assert result.console_output == ["120"]


def test_fibonacci_template_computes_correctly():
    result = _run("fibonacci", ["5"])
    assert result.status == "completed"
    assert result.console_output == ["0", "1", "1", "2", "3"]


def test_gcd_template_computes_correctly():
    result = _run("gcd", ["48", "18"])
    assert result.status == "completed"
    assert result.console_output == ["6"]


@pytest.mark.parametrize("n,expected", [("7", "Prime"), ("8", "Not Prime"), ("2", "Prime"), ("1", "Not Prime")])
def test_prime_check_template_computes_correctly(n, expected):
    result = _run("prime_check", [n])
    assert result.status == "completed"
    assert result.console_output == [expected]


def test_sum_of_digits_template_computes_correctly():
    result = _run("sum_of_digits", ["1234"])
    assert result.status == "completed"
    assert result.console_output == ["10"]


@pytest.mark.parametrize("n,expected", [("153", "Armstrong Number"), ("154", "Not an Armstrong Number")])
def test_armstrong_template_computes_correctly(n, expected):
    result = _run("armstrong", [n])
    assert result.status == "completed"
    assert result.console_output == [expected]


def test_non_executable_templates_are_marked_and_dont_crash_layout():
    non_executable = [t for t in TEMPLATE_REGISTRY if not t.executable]
    assert len(non_executable) > 0
    for t in non_executable:
        _, nodes, edges, warnings = load_template_flowchart(t.id)
        assert len(nodes) > 0
