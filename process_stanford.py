#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import phonenumbers
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'http://www-cs.stanford.edu/directory/undergraduate-students':
        util.Title.UNDERGRAD,
    'http://www-cs.stanford.edu/directory/masters-students': util.Title.MASTER,
    'http://www-cs.stanford.edu/directory/phd-students': util.Title.PHD,
    'http://www-cs.stanford.edu/directory/undergraduate-alumni':
        util.Title.UNDERGRAD_ALUMNI,
    'http://www-cs.stanford.edu/directory/masters-alumni':
        util.Title.MASTER_ALUMNI,
    'http://www-cs.stanford.edu/directory/phd-alumni': util.Title.PHD_ALUMNI,
}

PAGE_COUNT_PREFIX = '<i>Page 1 of '
PAGE_COUNT_SUFFIX = '</i>'

counts = {
    util.Title.UNDERGRAD: 0,
    util.Title.MASTER: 0,
    util.Title.PHD: 0,
    util.Title.UNDERGRAD_ALUMNI: 0,
    util.Title.MASTER_ALUMNI: 0,
    util.Title.PHD_ALUMNI: 0,
}

def download(url, page, output_dir):
  output_file = '%s/page-%d.html' % (output_dir, page)
  if os.path.isfile(output_file) and not util.OVERWRITE_DOWNLOAD:
    print '%s exists and not overwritable' % output_file
    return output_file

  util.wait()
  cmd = '%s --post-data page=%d %s -O %s -q' % (
      util.WGET, page, url, output_file)
  print 'running command: %s' % cmd
  assert os.system(cmd) == 0
  return output_file

def parse_page_count(afile):
  with open(afile, 'r') as fp:
    content = fp.read()
  p = content.find(PAGE_COUNT_PREFIX)
  assert p >= 0
  q = content.find(PAGE_COUNT_SUFFIX, p)
  assert q >= 0
  return int(content[p+len(PAGE_COUNT_PREFIX):q])

def find_table(soup):
  tables = soup.find_all('table')
  assert len(tables) == 1, 'expecting %d tables, got %d' % (
      1, len(tables))
  return tables[0]

def find_rows(table):
  rows = table.find_all('tr')
  assert len(rows) > 0
  assert len(rows[0].find_all('th')) == 4, (
      'expecting first row to be header: %s' % rows[0])
  return rows[1:]

def sanitize_phone(phone):
  # TODO: some numbers are not US-based.
  #assert phonenumbers.is_valid_number(phonenumbers.parse(phone, 'US')), (
  #    'invalid phone: %s' % phone)
  return phone

def sanitize_email(email):
  if email.find('@') < 0:
    email = '%s@stanford.edu' % email
  # TODO: failed with richards..antonorsi@stanford.edu
  #assert validate_email(email), 'invalid email: %s' % email
  return email

def sanitize_web(web):
  # TODO: failed with http://3;1;1;128;128;1;0xwww.stanford.edu/~whua
  #validate = URLValidator()
  #try:
  #  validate(web)
  #except ValidationError:
  #  assert False, 'invalid web: %s' % web
  return web

def count(items):
  for item in items:
    counts[item['title']] += 1

def process(afile, title, output_dir):
  p = afile.rfind('/') + 1
  assert p > 0
  q = afile.rfind('.')
  assert q > p
  output_file = '%s/%s.txt' % (output_dir, afile[p:q])
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file

  soup = BeautifulSoup(open(afile), 'html.parser')
  table = find_table(soup)
  rows = find_rows(soup)

  items = []
  for row in rows:
    cells = row.find_all('td')
    assert len(cells) == 4, 'expecting %d cells, got %d: %s' % (
        4, len(cells), cells)
    name = cells[0].get_text().strip()
    email = cells[3].get_text().strip()

    assert name != '', 'missing name: %s' % row
    item = {'name': name, 'title': title}
    if email != '':
      item['email'] = sanitize_email(email)
    items.append(item)
  count(items)

  with open(output_file, 'w') as fp:
    for item in items:
      print >> fp, item

def download_and_process(url, title, page, download_dir, processed_dir):
  downloaded_file = download(url, page, download_dir)
  processed_file = process(downloaded_file, title, processed_dir)
  return [downloaded_file, processed_file]

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
    downloaded_file, _ = download_and_process(
        url, subdir, 1, download_dir, processed_dir)
    page_count = parse_page_count(downloaded_file)
    print 'page count: %d' % page_count
    for i in range(2, page_count + 1):
      download_and_process(url, subdir, i, download_dir, processed_dir)
  print counts

if __name__ == '__main__':
  main()

