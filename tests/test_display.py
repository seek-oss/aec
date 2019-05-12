from tools.display import as_table, pretty


def test_as_table():
    assert as_table(['a', 'b'], [{'a': 1, 'b': 2}, {'b': 4, 'a': 3}]) == [['a', 'b'], ['1', '2'], ['3', '4']]


def test_pretty():
    table = [['a', 'b', 'c'], ['aaaaaaaaaa', 'b', 'c'], ['a', 'bbbbbbbbbb', 'c']]
    expected = (f"a           b           c  \n"
                f"aaaaaaaaaa  b           c  \n"
                f"a           bbbbbbbbbb  c  ")
    actual = pretty(table)
    assert actual == expected
