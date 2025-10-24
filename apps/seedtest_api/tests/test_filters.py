import os

from ..services.filters import parse_int_list, parse_str_list


def test_parse_str_list_basic():
    assert parse_str_list("algebra, geometry proof") == ["algebra", "geometry", "proof"]
    assert parse_str_list("  a,  b   c  , d  ") == ["a", "b", "c", "d"]
    assert parse_str_list(None) == []
    assert parse_str_list("") == []


def test_parse_int_list_basic():
    assert parse_int_list("10, 12 15") == [10, 12, 15]
    assert parse_int_list(" 1 , x 2  ") == [1, 2]
    assert parse_int_list(None) == []
    assert parse_int_list("") == []
