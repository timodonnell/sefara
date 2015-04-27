from nose.tools import eq_
import sefara
from . import data_path

def test_ex1():
    rc = sefara.load(data_path("ex1.json"))   
    context = {
        "foo": "bar",
        "baz": [7.6, "hello"],
        "sub1": "something-bar",
        "sub2": {
            "seven": "eight",
        },
    }
    eq_(rc.context.sub1, "something-bar")
    eq_(rc.context, context)
    eq_(rc.resources["dataset1"].name, "dataset1")
    eq_(rc.resources["dataset1"].something, "something-bar")
    eq_(rc.resources["dataset2"].name, "dataset2")
    eq_(len(rc.resources), 4)
    eq_(rc.tags, set(["alpha", "beta", "gamma", "delta", "sigma", "four"]))
