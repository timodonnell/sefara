from nose.tools import eq_
import sefara

def test_ex1():
    rc = sefara.load("data/ex1.json")
    context = {
        "foo": "bar",
        "baz": [7.6, "hello"],
        "sub1": "something-bar"
    }
    eq_(rc.context.sub1, "something-bar")
    eq_(rc.context, context)
    eq_(rc.resources["dataset1"].name, "dataset1")
    eq_(rc.resources["dataset2"].name, "dataset2")
    eq_(len(rc.resources), 2)
