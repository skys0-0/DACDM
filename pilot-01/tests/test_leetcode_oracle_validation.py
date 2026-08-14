from __future__ import annotations

from dacdm.leetcode_oracle_validation import (
    classify_constraint_coverage,
    extract_bound_constraints,
    parse_input_params,
)


def test_extracts_html_superscript_length_and_scalar_bounds() -> None:
    description = """
    <ul>
      <li><code>1 &lt;= nums.length &lt;= 10<sup>5</sup></code></li>
      <li><code>1 &lt;= k &lt;= 100</code></li>
    </ul>
    """
    constraints = extract_bound_constraints(description)
    assert [(row.name, row.kind, row.low, row.high) for row in constraints] == [
        ("k", "scalar", 1, 100),
        ("nums", "length", 1, 100000),
    ]


def test_parses_named_leetcode_inputs() -> None:
    params = parse_input_params('nums = [1, 2, 3], k = 2, s = "abc"')
    assert params == {"nums": [1, 2, 3], "k": 2, "s": "abc"}


def test_coverage_requires_exact_documented_boundary_for_edge() -> None:
    description = "1 <= nums.length <= 5; 1 <= k <= 4"
    input_output = [
        {"input": "nums = [2, 3], k = 2", "output": "0"},
        {"input": "nums = [9], k = 3", "output": "1"},
    ]
    coverage = classify_constraint_coverage(description, input_output)
    assert coverage["mapped_constraint_count"] == 2
    assert coverage["ordinary_case_supported"] is True
    assert coverage["edge_case_supported"] is True
    assert coverage["ordinary_case_count"] >= 1
    assert coverage["edge_case_count"] == 1


def test_no_boundary_match_does_not_invent_edge_evidence() -> None:
    description = "1 <= nums.length <= 100; 1 <= k <= 50"
    input_output = [
        {"input": "nums = [2, 3, 4], k = 2", "output": "0"},
        {"input": "nums = [5, 6], k = 4", "output": "1"},
    ]
    coverage = classify_constraint_coverage(description, input_output)
    assert coverage["ordinary_case_supported"] is True
    assert coverage["edge_case_supported"] is False


def test_element_and_nested_length_constraints_are_supported() -> None:
    description = "0 <= nums[i] <= 9; 1 <= grid[i].length <= 3"
    input_output = [
        {"input": "nums = [0, 5], grid = [[1], [2, 3]]", "output": "1"}
    ]
    coverage = classify_constraint_coverage(description, input_output)
    assert coverage["edge_case_supported"] is True
    assert coverage["mapped_constraint_count"] == 2
