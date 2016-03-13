#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import urllib
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'http://www.ics.uci.edu/about/search/search_graduate_all.php':
        util.Title.GRAD,
}
HREF_EMAIL_PREFIX = 'mailto:'

counts = {
    'total': 0,
}

def download(url, download_dir):
  output_file = '%s/page-1.html' % download_dir
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def process_grad(download_file):
  # Use lxml to be lenient; the html table is malformed.
  soup = BeautifulSoup(open(download_file), 'lxml')
  tables = soup.find_all('table')
  assert len(tables) == 1, 'expecting %d tables, got %d: %s' % (
      1, len(tables), download_file)
  trs = tables[0].find_all('tr')
  items = []
  for tr in trs:
    tds = tr.find_all('td')
    assert len(tds) == 1
    name = tds[0].get_text().strip()
    p = name.find('|')
    if p > 0:
      assert name[p+1:].strip() == 'Website', tds[0]
      name = name[:p].strip()
    a = tds[0].find_all('a')
    assert len(a) > 0
    assert a[0]['href'].startswith(HREF_EMAIL_PREFIX)
    email = urllib.unquote(a[0]['href'][len(HREF_EMAIL_PREFIX):]).strip()
    item = {'name': name, 'email': email, 'title': util.Title.GRAD}
    counts['total'] += 1
    items.append(item)
  return items

def process(download_file, processed_dir):
  output_file = '%s/page-1.txt' % processed_dir
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file
  items = process_grad(download_file)
  with open(output_file, 'w') as fp:
    for item in items:
      print >> fp, item

def download_and_process(url, download_dir, processed_dir):
  download_file = download(url, download_dir)
  process(download_file, processed_dir)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--download_dir', required=True)
  parser.add_argument('--processed_dir', required=True)
  args = parser.parse_args()

  util.prepare_dirs(URL_SUBDIR_MAP, args.download_dir, args.processed_dir)
  for url, subdir in URL_SUBDIR_MAP.iteritems():
    print 'processing %s => %s' % (url, subdir)
    download_dir = '%s/%s' % (args.download_dir, subdir)
    processed_dir = '%s/%s' % (args.processed_dir, subdir)
    download_and_process(url, download_dir, processed_dir)
  print counts

if __name__ == '__main__':
  main()

