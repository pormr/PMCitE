# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 13:29:41 2020

PMCitE - PubMed Citation Extractor

A utility to query the NCBI database for citation data/bibliography.

@author: pormr
"""

import os
#import re
import requests
from tkinter import Tk
from tkinter.filedialog import asksaveasfilename


# Prompt for PMID
# TODO: Add functionality for resolving DOIs
print('PMCitE - A utility to query the NCBI database for citation data/bibliography.')
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
        # Other unhandled network errors go here
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
csrftoken = s.cookies['pm-csrf']

# Prompt for the filename
Tk_root = Tk()
Tk_root.withdraw()
format_mapping = {'nbib': 'pubmed', 'csv': 'csv', 'txt': 'summary-text',
                  '~pmid': 'pmid', '~abs': 'abstract', '~sum': 'summary-text'}
file_types = [('NBIB Formatted File (PubMed) (*.nbib)', '*.nbib'),
              ('Comma Separated Values (CSV) File (*.csv)', '*.csv'),
              ('Text File (PMIDs) (*.txt)', ('*.~pmid', '*.txt')),
              ('Text File (Summary) (*.txt)', ('*.~sum', '*.txt')),
              ('Text File (Abstract) (*.txt)', ('*.~abs', '*.txt')),
              ('All Files (*.*)', '*.*')]
default_name = "pubmed-%i.nbib" % PMID
default_dir = os.path.normpath(os.path.expanduser("~/Desktop"))
filename = asksaveasfilename(initialfile = default_name,
                             filetypes = file_types,
                             defaultextension = file_types,
                             initialdir = default_dir)

# Replace the dummy extensions
if filename:
    tmp = filename.split('.')
    result_format = format_mapping.get(tmp[-1], 'pmid')
    if '~' in tmp[-1]:
        tmp[-1] = 'txt'
        filename = '.'.join(tmp)
else:
    print('Saving aborted.')
    os._exit(0)

# Prepare the request
headers={'Referer': query_URI % PMID + '#'}
post_data = {'csrfmiddlewaretoken': csrftoken,
             'results-format': result_format,
             'term': '',
             'term_alias': 'LINKSET|pubmed_pubmed_refs|%i' % PMID}
result = s.post(post_URI, data=post_data, headers=headers, stream=True)


# Write raw data to the file
try:
    f = open(filename,"wb")
    for chunk in result.iter_content(chunk_size=512):
        if chunk:
            f.write(chunk)  # TODO: Add progress bar?
except IOError:
    print("IO Error : Unable to save result to file.")
    os._exit(0)
finally:
    f.close()

