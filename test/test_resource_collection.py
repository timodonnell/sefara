from nose.tools import eq_
import sefara

def test_ex1():
    rc = sefara.load("data/ex1.hjson")
    common = {
        "foo": "bar",
        "baz": [7.6, "hello"],
    }
    eq_(rc.common, common)
    eq_(rc.resources[0].name, "dataset1")
    eq_(rc.resources[1].name, "dataset2")
    eq_(len(rc.resources), 2)
    
    
