## Dataset

- `mapping/` : `mapping` folder the test.txt, train.txt, val.txt files. This files contains the prefix of the file name for each dataset.
- `unsliced/` : `unsliced` folder contains the original dataset code.
- `sliced/`: `sliced` folder contains the dataset after applying slicing.

Each entry of the json files contains the following fields:
```
{
  "data_flow": {
      ....
  },
  "control_flow": {
      ....
  },
  "source": {
     ...
  },
  "buggy_line_num": <buggy_line_number>,
  "target": "correct_code", 
  "json_file": "name-of-the-json-file",
  "file_prefix": "file-name-prefix"
 },
```

Files in the `mapping` folder contains the prefix of the file name to show what are the files for the test, train and validation split. Based on the prefix, we understand whether a datapoint belongs to test, train or validation.






 

