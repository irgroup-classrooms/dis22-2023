import json
from querygpt.model import DatasetEntry
import pandas as pd

def read_dataset_jsonl(fn):
    dataset = []
    with open(fn, "r") as fp:
        line = fp.readline()
        while line != "":
            dse = DatasetEntry.from_json(line)
            dataset.append(dse)
            line = fp.readline()

    return dataset


def ds_to_df(ds: list[DatasetEntry]):
    rows_cleaned = []
    for entry in ds:
        rows_cleaned.extend(entry.extract_answers())
    return pd.DataFrame(rows_cleaned)