# eCourts India Case Listing Scraper
A Python-based command-line tool to fetch court case listings and details from the eCourts India portal.
---
## Command-Line Options
### Case Search Options

- ```--cnr CNR``` - Search by CNR number
- ```--case-type``` TYPE - Case type (CS, CRL, etc.)
- ```--case-number``` NUMBER - Case number
- ```--case-year``` YEAR - Filing year

###Listing Check Options

- ```--today``` - Check if listed today
- ```--tomorrow``` - Check if listed tomorrow

###Download Options

- ```--download-pdf``` - Download case PDF
- ```--causelist``` - Download full cause list (requires --today or --tomorrow)

###Configuration Options

- ```--state``` CODE - State code (default: DL for Delhi)
- ```--district``` CODE - District code (default: 1)
- ```--output-dir``` PATH - Output directory (default: output)
---
