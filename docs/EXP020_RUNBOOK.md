# EXP020 quick run

EXP020 trains the same YOLO11n architecture as EXP019, but makes Roboflow the
dominant training source. The default training mix is 70% Roboflow, 20% TACO,
5% dmedhi, and 5% TrashNet by image count.

The raw datasets are not changed. The generated dataset is written to
`datasets/exp020_roboflow_dominant/`, so EXP019 remains untouched.

## From the project folder

Install dependencies once:

```powershell
py -3 -m pip install -e ".[train]"
```

Prepare and inspect the source mix:

```powershell
py -3 scripts/run_exp020.py --prepare-only
Get-Content datasets/exp020_roboflow_dominant/source_summary.json
```

Train, validate, and export:

```powershell
py -3 scripts/run_exp020.py --train
```

If the dataset already exists and should be rebuilt:

```powershell
py -3 scripts/run_exp020.py --prepare-only --force
```

The script expects these existing source directories:

- `datasets/roboflow_raw`
- `datasets/taco_raw`
- `datasets/trashnet_labeled`
- `datasets/raw/dmedhi`

Before camera deployment, evaluate the resulting model on the same real camera
sequence used to compare EXP014 and EXP019. Record recall, precision, false
positives, and confidence; confidence alone is not an accuracy measurement.
