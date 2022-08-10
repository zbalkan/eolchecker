# EOL checker

EOL Checker is a simple application which gathers EOL information for software and hardware and allows you to query locally.

## Getting Started

```bash
usage: eol_checker.py [-h] [--software QUERY_SOFTWARE] [--hardware QUERY_HARDWARE] [-u]

Query EOL software or hardware.

options:
  -h, --help            show this help message and exit
  --software QUERY_SOFTWARE
                        Query the software by name
  --hardware QUERY_HARDWARE
                        Query the software by name
  -u, --update          Updates the local database. When combined with a query, it updates the database before running the query.
```

## Thanks

The information for the software is based on data provided by [endoflife.date](https://endoflife.date) project. Hardware information is parsed from [Hardware Wartung website](https://www.hardwarewartung.com/en/).
