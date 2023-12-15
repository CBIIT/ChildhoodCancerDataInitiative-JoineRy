# ChildhoodCancerDataInitiative-JoineRy
Takes a set of TSV outputs from the CCDI Explorer, concatenates and restores ids to match the given CCDI template.

To run the script, run the following command in a terminal where python3 is installed for help.

```
python CCDI-JoineRy.py -h
```
```
usage: CCDI-JoineRy.py [-h] -d DIRECTORY -t TEMPLATE

Takes a set of TSV outputs from the CCDI Explorer, concatenates and restores ids to match the given CCDI template.

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  -d DIRECTORY, --directory DIRECTORY
                        directory of tsv node files
  -t TEMPLATE, --template TEMPLATE
                        dataset template file, CCDI_submission_metadata_template.xlsx
```
