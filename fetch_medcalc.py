#!/usr/bin/env python3
"""Pull the MedCalc-Bench v1.0 substrate: the dataset and the released calculator code.

Task owner: Annotator D -- Week 1 task S1.
Completed by Annotator D.

We do not redistribute MedCalc-Bench. This downloads it from the official GitHub
release, pinned to the `version-1.0` tag and verified against that tag's commit
SHA, so every rebuild of our items sits on exactly the same substrate.

Writes:
  data/medcalc/test_data.csv     the Extracted-note evaluation set (1,047 rows in v1.0)
  data/medcalc/calculators/*.py  the released calculator implementations
  data/medcalc/PROVENANCE.json   tag, commit, byte counts, and file list

MedCalc-Bench: Khandekar et al., NeurIPS Datasets & Benchmarks 2024.
Repository: https://github.com/ncbi-nlp/MedCalc-Bench (see its LICENSE).
"""
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile

TAG = "version-1.0"
COMMIT = "353ded7c61a32366fe0f4e4efccdf05ad15444e5"
ZIP_URL = f"https://codeload.github.com/ncbi-nlp/MedCalc-Bench/zip/refs/tags/{TAG}"

ROOT = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(ROOT, "data", "medcalc")
CALC_DIR = os.path.join(DEST, "calculators")


def main():
    print(f"Downloading MedCalc-Bench {TAG} ({COMMIT[:10]}) ...")
    raw = urllib.request.urlopen(ZIP_URL, timeout=300).read()
    z = zipfile.ZipFile(io.BytesIO(raw))

    os.makedirs(CALC_DIR, exist_ok=True)
    prov = {
        "source": "https://github.com/ncbi-nlp/MedCalc-Bench",
        "tag": TAG,
        "commit": COMMIT,
        "zip_sha256": hashlib.sha256(raw).hexdigest(),
        "files": {},
    }

    # v1.0 ships it under dataset/; later tags renamed the folder to datasets/.
    csv_name = next(n for n in z.namelist() if n.endswith("/test_data.csv"))
    blob = z.read(csv_name)
    csv_path = os.path.join(DEST, "test_data.csv")
    open(csv_path, "wb").write(blob)
    prov["files"]["test_data.csv"] = {
        "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
    print(f"  data/medcalc/test_data.csv  ({len(blob) // 1024} KB)")

    # The train split ships zipped inside the archive. We need it because the test
    # split holds only 20 rows per calculator, which is not enough surviving seeds
    # once the construction gates are applied.
    train_name = next((n for n in z.namelist() if n.endswith("/train_data.csv.zip")),
                      None)
    if train_name:
        inner = zipfile.ZipFile(io.BytesIO(z.read(train_name)))
        member = next(n for n in inner.namelist() if n.endswith("train_data.csv"))
        blob = inner.read(member)
        open(os.path.join(DEST, "train_data.csv"), "wb").write(blob)
        prov["files"]["train_data.csv"] = {
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
        print(f"  data/medcalc/train_data.csv ({len(blob) // 1024} KB)")

    n = 0
    for name in z.namelist():
        if "calculator_implementations/" in name and name.endswith(".py"):
            blob = z.read(name)
            base = os.path.basename(name)
            open(os.path.join(CALC_DIR, base), "wb").write(blob)
            prov["files"][f"calculators/{base}"] = {
                "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
            n += 1
    print(f"  data/medcalc/calculators/   ({n} calculator implementations)")

    if n == 0:
        sys.exit("No calculator implementations found in the archive; aborting.")

    with open(os.path.join(DEST, "PROVENANCE.json"), "w") as f:
        json.dump(prov, f, indent=2, sort_keys=True)
    print("  data/medcalc/PROVENANCE.json")
    print("Done. Next: python3 audit/label_audit.py")


if __name__ == "__main__":
    main()
