# pathase

Work in progress.

```
resources = load_from_file("/Users/tim/sinai/git/ovarian-cancer/projects/pt189/datasets.hjson")

# Add paths to my files
def add_path(resource):
    sshfs_path = "/".join(["/Users/tim/mount/demeter", resources.common.base_path_nfs, resource.path])
    return resource + {"sshfs_path": sshfs_path}
resources = resources.derive(resources = add_path)

print(resources.summary)

#print(resources.with_tag("+proton").with_tag("exome").summary)
#print(resources.with_name("tumor_secondary_pelvic_sidewalls_rna_illumina1").summary)
```