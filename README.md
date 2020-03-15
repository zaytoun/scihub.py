scihub.py
[![Python](https://img.shields.io/badge/Python-3%2B-blue.svg)](https://www.python.org)
=========

scihub.py is an unofficial API for sci-hub. scihub.py can search for papers on Google Scholars and download papers from a sci-hub website. It can be imported independently or used from the command-line.

If you believe in open access to scientific papers, please donate to Sci-Hub.

Features
--------
* Download specific articles directly or via a sci-hub website
* Download a collection of articles by passing in file of article identifiers
* Search for articles on Google Scholars and download them

**Note**: A known limitation of scihub.py is that captchas show up every now and then, blocking any searches or downloads.

Setup
-----
```
pip install -r requirements.txt
```

Usage
------
You can interact with scihub.py from the commandline:

```
usage: scihub.py [-h] [-d (DOI|PMID|URL)] [-f path] [-s query] [-sd query]
                 [-l N] [-o path] [-v]
                 sci_hub_url

SciHub - To remove all barriers in the way of science.

positional arguments:
  sci_hub_url           set scihub website URL

optional arguments:
  -h, --help            show this help message and exit
  -d (DOI|PMID|URL), --download (DOI|PMID|URL)
                        tries to find and download the paper
  -f path, --file path  pass file with list of identifiers and download each
  -s query, --search query
                        search Google Scholars
  -sd query, --search_download query
                        search Google Scholars and download if possible
  -l N, --limit N       the number of search results to limit to
  -o path, --output path
                        directory to store papers
  -v, --verbose         increase output verbosity
  -p, --proxy           set proxy
```

You can also import scihub. The following examples below demonstrate all the features.

### fetch

```
from scihub import SciHub

sh = SciHub(SCI_HUB_URL)

# fetch specific article (don't download to disk)
# this will return a dictionary in the form 
# {'pdf': PDF_DATA,
#  'url': SOURCE_URL,
#  'name': UNIQUE_GENERATED NAME
# }
result = sh.fetch('http://ieeexplore.ieee.org/xpl/login.jsp?tp=&arnumber=1648853')
```

### download

```
from scihub import SciHub

    sh = SciHub(SCI_HUB_URL)

# exactly the same thing as fetch except downloads the articles to disk
# if no path given, a unique name will be used as the file name
result = sh.download('http://ieeexplore.ieee.org/xpl/login.jsp?tp=&arnumber=1648853', path='paper.pdf')
```

### search

```
from scihub import SciHub

sh = SciHub(SCI_HUB_URL)

# retrieve 5 articles on Google Scholars related to 'bittorrent'
results = sh.search('bittorrent', 5)

# download the papers; will use sci-hub.io if it must
for paper in results['papers']:
	sh.download(paper['url'])

```
License
-------
MIT










