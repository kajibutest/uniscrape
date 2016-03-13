#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'https://www.cs.wisc.edu/people/graduate-students': util.Title.GRAD,
    'https://www.cs.wisc.edu/people/undergraduate-students': util.Title.UNDERGRAD,
}

LI_CLASS = 'views-row'
NAME_DIV_CLASS = 'views-field-field-full-name'
EMAIL_DIV_CLASS = 'views-field-views-conditional'

counts = {
    util.Title.GRAD: 0,
    util.Title.UNDERGRAD: 0,
}

def download(url, download_dir):
  output_file = '%s/page-1.html' % download_dir
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def process(download_file, key, processed_dir):
  output_file = '%s/page-1.txt' % processed_dir
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file
  soup = BeautifulSoup(open(download_file), 'html.parser')
  lis = soup.find_all('li', class_=LI_CLASS)
  items = []
  for li in lis:
    divs = li.find_all('div', class_=NAME_DIV_CLASS)
    assert len(divs) == 1, li
    name = divs[0].get_text().strip()
    assert name != '', li
    divs = li.find_all('div', class_=EMAIL_DIV_CLASS)
    assert len(divs) == 1, li
    a = divs[0].find_all('a')
    email = ''
    if len(a) > 0:
      assert len(a) == 1, li
      email = a[0].get_text().strip()
      assert a[0]['href'].strip() == 'mailto:%s' % email, li
    item = {'name': name, 'title': key}
    counts[key] += 1
    if email != '':
      item['email'] = email
    items.append(item)
  with open(output_file, 'w') as fp:
    for item in items:
      print >> fp, item

def download_and_process(url, key, download_dir, processed_dir):
  download_file = download(url, download_dir)
  process(download_file, key, processed_dir)

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
    download_and_process(url, subdir, download_dir, processed_dir)
  print counts

if __name__ == '__main__':
  main()

