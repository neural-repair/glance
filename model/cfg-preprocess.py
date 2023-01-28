import json
import glob
import traceback

train_files_expected = {}
test_files_expected = {}
val_files_expected = {}

train_files_actual = []
test_files_actual = []
val_files_actual = []

with open(f"./model-artifacts/raw-expected/train.txt") as train_file:
    lines = train_file.readlines()
    for file_prefix in lines:
        file_prefix = file_prefix.strip()
        train_files_expected[file_prefix] = file_prefix

with open(f"./model-artifacts/raw-expected/test.txt") as test_file:
    lines = test_file.readlines()
    for file_prefix in lines:
        file_prefix = file_prefix.strip()
        test_files_expected[file_prefix] = file_prefix

with open(f"./model-artifacts/raw-expected/val.txt") as val_file:
    lines = val_file.readlines()
    for file_prefix in lines:
        file_prefix = file_prefix.strip()
        val_files_expected[file_prefix] = file_prefix


def process_metadata_file(input_file):
    with open(input_file, 'r') as f:
        all_metadata = json.load(f)
        num_of_files = 0
        num_of_train_files = 0
        num_of_test_files = 0
        num_of_val_files = 0
        num_of_missing_prefix = 0

        for metadata in all_metadata:
            if "file_prefix" in metadata:
                num_of_files += 1
                prefix = metadata["file_prefix"]
                if not prefix.startswith("file_prefix"):
                    prefix = "SHIFT_" + prefix

                if prefix in train_files_expected:
                    train_files_actual.append(prefix)
                    num_of_train_files += 1
                elif prefix in test_files_expected:
                    test_files_actual.append(prefix)
                    num_of_test_files += 1
                elif prefix in val_files_expected:
                    val_files_actual.append(prefix)
                    num_of_val_files += 1
                else:
                    num_of_missing_prefix += 1
                    #print(f"prefix:{prefix} missing in train, test, or val file list.")

                with open(f"./model-artifacts/merged-dataset/{prefix}-buggy.txt", 'w') as buggy:
                    json.dump(metadata, buggy)
                with open(f"./model-artifacts/merged-dataset/{prefix}-correct.txt", 'w') as correct:
                    correct.write(metadata["target"])

    return num_of_files, num_of_train_files, num_of_test_files, num_of_val_files, num_of_missing_prefix


metadata_files = glob.glob("./model-artifacts/single/metadata_*.json")
for metadata_file in metadata_files:
    (number_of_files, number_of_train_files, number_of_test_files, number_of_val_files, number_of_missing_prefix) = process_metadata_file(metadata_file)
    print(f"file: {metadata_file}, number_of_files: {number_of_files}, "
          f"number_of_train_files={number_of_train_files}, "
          f"number_of_test_files={number_of_test_files}, "
          f"number_of_val_files={number_of_val_files}, "
          f"number_of_missing_prefix={number_of_missing_prefix}, "
          f"")

    with open(f"./model-artifacts/raw/train.txt", "w") as raw_train_file:
        raw_train_file.write('\n'.join(str(element) for element in train_files_actual))

    with open(f"./model-artifacts/raw/test.txt", "w") as raw_test_file:
        raw_test_file.write('\n'.join(str(element) for element in test_files_actual))

    with open(f"./model-artifacts/raw/val.txt", "w") as raw_val_file:
        raw_val_file.write('\n'.join(str(element) for element in val_files_actual))