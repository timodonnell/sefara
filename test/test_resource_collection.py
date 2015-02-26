from nose.tools import eq_
import pathase

def test_ex1():
    rc = pathase.load("data/ex1.hjson")
    common = {
        "foo": "bar",
        "baz": [7.6, "hello"],
    }
    eq_(rc.common, common)
    eq_(rc.resources[0].name, "dataset1")
    