from sefara import export

export(
    "patientA_sequencing_blood_2010",
    path="/path/to/file1.bam",
    tags=["patient_A", "sequencing", "2010"],
    capture_kit="Agilent sureselect",
    description="Sample taken from normal blood"
)

export(
    "patientA_sequencing_tumor_2012",
    path="/path/to/file2.bam",
    tags=["patient_A", "sequencing", "2012"],
    capture_kit="Nimblegen",
    description="Primary tumor, left ovary"
)

export(
    "patientB_sequencing_normal_tissue_2012",
    path="/path/to/file3.bam",
    tags=["patient_B", "sequencing", "2012"],
    capture_kit="unknown",
    description="Matched normal tissue, pancreas"
)

export(
    "patientB_sequencing_tumor_2014",
    path="/path/to/file4.bam",
    tags=["patient_B", "sequencing", "2014"],
    capture_kit="Agilent sureselect",
    description="liver metastasis"
)

export(
    "patientA_somatic_variant_calls",
    path="/path/to/variants.vcf",
    tags=["patient_A", "variants"],
    tool="strelka",
    normal_reads="patientA_sequencing_blood_2010",
    tumor_reads="patientA_sequencing_tumor_2012"
)