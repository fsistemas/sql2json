# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.10] - 2020-05-25

### Added
- Add support to write output to csv, excel or json file using --output sales.csv, --output sales.csv, --output sales.json
- New parameter output, the name of the file to write the data. With custom variables like --output Sales-{CURRENT_DATE-5}_{CURRENT_DATE+2}
- New parameter format(default=json). Values json, csv, excel
- Add examples to README.md for output, format

## [0.1.9] - 2020-01-19

### Added
- Support map column value as key, value ussing --key column1 --value column2
- Add README.md, improve documentation

### Removed
- README.rst

## [0.1.8] - 2020-01-18

### Added
- Support map column value as key, value ussing --key column1 --value column2
- New flag jsonkeys: coma separated columns to convert JSON functions result as JSON not as string

## [0.1.7] - 2020-01-04

### Added
- Support to read sql from external file using --query @FULL_PATH_TO_MY_FILE
- You can pass a custom config file as parameter --config. Ex. --config /Users/myuser/my-config.json

### Changed
- FIX to accept any parameter, not only date formulas
- Remove empty flag: true/false from response when user pass wrapper flag
