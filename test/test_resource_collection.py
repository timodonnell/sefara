from nose.tools import eq_
import sefara
from . import data_path

def Xtest_ex1_json():
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

def test_ex1_py():
    rc = sefara.load(data_path("ex1.py"))
    print(rc)
    eq_(rc["dataset1"].name, "dataset1")
    eq_(rc["dataset1"].something, "something-bar")

    dataset1 = rc.resources["dataset1"]
    tags = list(dataset1.tags)
    eq_(tags, ["alpha", "beta"])

    eq_(rc.resources["dataset2"].name, "dataset2")
    eq_(len(rc.resources), 4)
    eq_(rc.tags,
        set(["alpha", "beta", "gamma", "delta", "sigma", "four", "b"]))

    eq_([x.name for x in rc.filter("tags.gamma")],
        ["dataset2", "dataset3", "dataset4"])

    eq_([x.name for x in rc.filter("tags.gamma and tags.sigma")],
        ["dataset3", "dataset4"])

    eq_(rc.filter("all([tags.gamma, tags.sigma, not tags.b])").singleton(),
        rc["dataset4"])

    eq_([x.name for x in rc.filter(lambda resource: resource.tags.gamma)],
        ["dataset2", "dataset3", "dataset4"])

def test_decorate_ex1_py():
    rc = sefara.load(data_path("ex1.py"))
    rc.decorate(data_path("decorate_ex1.py"))
    eq_(rc["dataset1"].posix_path, "/path/to/dataset1.bam")

def test_roundtrip_to_json():
    rc = sefara.load(data_path("ex1.py"))
    json = rc.to_json()
    rc2 = sefara.loads(json, format="json")
    eq_(rc, rc2)



