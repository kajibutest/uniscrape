#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'http://www.cs.usc.edu/faculty_staff/phds/': 'phd',
}
HREF_EMAIL_PREFIX = 'mailto:'

counts = {
    'total': 0,
    'email': 0,
}

def download(url, download_dir):
  output_file = '%s/page-1.html' % download_dir
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def process_phd(download_file):
  soup = BeautifulSoup(open(download_file), 'html.parser')
  tables = soup.find_all('table')
  assert len(tables) == 2, 'expecting %d tables, got %d: %s' % (
      2, len(tables), download_file)
  trs = tables[1].find_all('tr')
  assert len(trs) > 0
  tds = trs[0].find_all('td')
  assert (len(tds) == 3
          and tds[0].get_text().strip() == 'Name'
          and tds[1].get_text().strip() == 'Email'
          and tds[2].get_text().strip() == 'Faculty Advisor(s)'), (
      'unexpected table header: %s' % trs[0])
  items = []
  for i in range(1, len(trs)):
    tds = trs[i].find_all('td')
    assert len(tds) == 3
    name = tds[0].get_text().strip()
    try:
      last, first = name.split(',')
    except ValueError:
      assert False, name
    name = '%s %s' % (first.strip(), last.strip())
    email = tds[1].get_text().strip()
    a = tds[1].find_all('a')
    if len(a) > 0:
      assert len(a) == 1
      href = a[0]['href'].strip()
      if not href.endswith(email):
        print 'inconsistent email: %s vs %s' % (href, email)
        if href.startswith(HREF_EMAIL_PREFIX):
          email = href[len(HREF_EMAIL_PREFIX):]
        print 'using: %s' % email
    item = {'name': name, 'title': util.Title.PHD}
    counts['total'] += 1
    if email != '':
      item['email'] = email
      counts['email'] += 1
    items.append(item)
  return items

def process(download_file, processed_dir):
  output_file = '%s/page-1.txt' % processed_dir
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file
  items = process_phd(download_file)
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

