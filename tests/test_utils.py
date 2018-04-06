from workspace.utils import shortest_id


def test_shortest_id():
    assert shortest_id('apple', ['orange', 'banana']) == 'a'
    assert shortest_id('apple', ['apricot', 'banana']) == 'app'
    assert shortest_id('apple', ['apple seed', 'banana']) == 'apple'
    assert shortest_id('apple', ['apple', 'banana']) == 'a'
