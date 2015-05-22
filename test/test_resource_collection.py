from nose.tools import eq_
import sefara
from . import data_path

def test_ex1_py():
    rc = sefara.load(data_path("ex1.py"))
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

def test_ex1_py_from_uri():
    rc = sefara.load(data_path("ex1.py#filter=tags.gamma"))
    eq_([x.name for x in rc],
        ["dataset2", "dataset3", "dataset4"])

    rc = sefara.load(
        "file://" + data_path("ex1.py#filter=tags.gamma&filter=tags.sigma"))
    eq_([x.name for x in rc],
        ["dataset3", "dataset4"])

def test_transform_ex1_py():
    rc = sefara.load("file://" + data_path("ex1.py"))
    rc.transform(data_path("transform_ex1.py"))
    eq_(rc["dataset1"].posix_path, "/path/to/dataset1.bam")

def test_transform_ex1_py_2():
    rc = sefara.load(data_path("ex1.py"))

    def transformer(rc):
        for r in rc:
            r.name = "bar-" + r.name
    rc.transform(transformer)
    eq_(rc["bar-dataset1"].name, "bar-dataset1")

def test_roundtrip():
    rc = sefara.load(data_path("ex1.py"))
    json = rc.to_json()
    rc2 = sefara.loads(json, format="json")
    eq_(rc, rc2)
    python = rc.to_python()
    rc3 = sefara.loads(python, format="python")
    eq_(rc, rc3)

