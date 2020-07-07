# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 13:29:41 2020

PMCitE - PubMed Citation Extractor

A utility to query the NCBI database for citation data/bibilography.

@author: pormr
"""

import os
import re
import requests
from tkinter import Tk
from tkinter.filedialog import asksaveasfile # asksaveasfilename


# Prompt for PMID
print('PMCitE - A utility to query the NCBI database for citation data/bibilography.')
while 1:
    try:
        PMID = int(input('Please input the PMID:\n'))
    except ValueError:
        print('Invalid PMID.')
    else:
        break

# Query the NCBI database for citation data
citation_URI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?db=pubmed&id=%i&cmd=neighbor&linkname=pubmed_pubmed_refs"
query_URI = "https://pubmed.ncbi.nlm.nih.gov/?linkname=pubmed_pubmed_refs&from_uid=%i"
post_URI = "https://pubmed.ncbi.nlm.nih.gov/results-export-search-data/"
retry_times = 3
for i in range(retry_times):
    try:
        citation_XML = requests.post(citation_URI % PMID, timeout=5)
    except requests.exceptions.Timeout:
        print('Connection timeout - Retry for %i time(s)' % (i + 1))
    except requests.exceptions.ReadTimeout:
        print('Read timeout - Retry for %i time(s)' % (i + 1))
    except requests.exceptions.SSLError:
        print('SSL error - Retry for %i time(s)' % (i + 1))
    except requests.exceptions.ConnectionError:
        # Other unhandled network errors goes here
        print('Connection error - please check your connection.')
        os._exit(0)
    else:
        break
else:
    # The loop will terminate after 3 attempts
    print('The NCBI API is not available now.')
    os._exit(0)

# Check the XML content for citation data
if 'LinkSetDb' not in citation_XML.text:
    print('Unable to find citation data for the specific PMID.')
    os._exit(0)

# Fetch the 'csrftoken'
s = requests.Session()
s.get(query_URI % PMID)
csrftoken = s.cookies['labs-pubmed-csrftoken']

# Prepare the request
headers={'Referer': query_URI % PMID + '#'}
post_data = {'csrfmiddlewaretoken': csrftoken,
             'results-format': 'pubmed',
             'term': '',
             'term_alias': 'LINKSET|pubmed_pubmed_refs|%i' % PMID}
result = s.post(post_URI, data=post_data, headers=headers, stream=True)

# Prompt for the filename and get the file handle
Tk_root = Tk()
Tk_root.withdraw()
file_types = [('NBIB Formatted File (PubMed) (*.nbib)', '*.nbib'),
              ('All Files (*.*)', '*.*')]
file = re.findall('filename="(.+)"', result.headers['Content-Disposition'])[0]
default_dir = os.path.normpath(os.path.expanduser("~/Desktop"))
f = asksaveasfile(initialfile = file,
                  filetypes = file_types,
                  defaultextension = file_types,
                  initialdir = default_dir,
                  mode = "wb")

# Write raw data to the file
for chunk in result.iter_content(chunk_size=512):
    if chunk:
        f.write(chunk)
f.close()
