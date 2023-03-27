import datetime

from dateutil.tz import tzutc

from aec.util.display import as_table


def test_as_table():
    assert as_table([{"a": 1, "b": 2}, {"b": 4, "a": 3}], ["a", "b"]) == [
        ["a", "b"],
        ["1", "2"],
        ["3", "4"],
    ]


def test_as_table_infer_keys():
    assert as_table([{"a": 1, "b": 2}, {"b": 4, "a": 3}]) == [
        ["a", "b"],
        ["1", "2"],
        ["3", "4"],
    ]


def test_as_table_with_datetime():
    assert as_table(
        [{"a": 1, "b": datetime.datetime(2019, 8, 19, 6, 3, 6, tzinfo=tzutc())}],
        ["a", "b"],
    ) == [
        ["a", "b"],
        ["1", "2019-08-19 06:03:06+00:00"],
    ]


def test_as_table_with_list():
    assert as_table(
        [{"a": 1, "b": ["x", "y"]}],
        ["a", "b"],
    ) == [
        ["a", "b"],
        ["1", "['x', 'y']"],
    ]


def test_as_table_with_none():
    assert as_table([{"a": 1, "b": None}]) == [["a", "b"], ["1", None]]


def test_as_table_empty_list():
    assert as_table([]) == []
