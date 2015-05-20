from sefara import export

export(
    "dataset1",
    path="/path/to/file1.csv",
    tags=["alpha", "beta"],
    foo="zzz",
    something="something-bar",
)

export(
    name="dataset2",
    path="/path/to/somewhere/else.bam",
    tags=["gamma", "delta", "alpha"],
    info="some description",
)

export("dataset3", **{
    "path": "/path/to/somewhere/else2.bam",
    "tags": ["gamma", "sigma", "alpha", "b"],
    "info": "some description"
})

export("dataset4", **{
    "path": "/path/to/somewhere/else3.bam",
    "tags": ["gamma", "sigma", "alpha", "four"],
    "info": "some description4",
})
