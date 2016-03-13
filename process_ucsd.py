#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import util

# Should always be true because url processing order may be different
# everytime (iterating through URL_SUBDIR_MAP).  TODO: fix this.
OVERWRITE_DOWNLOAD = True
OVERWRITE_PROCESSED = True

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    # Original url is http://www.cse.ucsd.edu/cse_directory
    # This link was identified as the url for requesting actual data.
    ('http://jacobsschool.ucsd.edu/about/about_contacts/'
     'directory_query.sfe?dept=cse'): 'dir',
    'http://www.cse.ucsd.edu/node/2545': 'phd',
    'http://www.cse.ucsd.edu/node/2260': 'phd',
    'http://www.cse.ucsd.edu/node/2157': 'phd',
    'http://www.cse.ucsd.edu/node/2063': 'phd',
    'http://www.cse.ucsd.edu/node/175': 'phd',
    'http://www.cse.ucsd.edu/node/176': 'phd',
    'http://www.cse.ucsd.edu/node/177': 'phd',
    'http://www.cse.ucsd.edu/node/178': 'phd',
    'http://www.cse.ucsd.edu/node/179': 'phd',
    'http://www.cse.ucsd.edu/node/180': 'phd',
    'http://www.cse.ucsd.edu/node/181': 'phd',
    'http://www.cse.ucsd.edu/node/182': 'phd',
}

DIR_SECTION = 'Researchers/Post-Docs/Visitors'
PHD_TITLE_PREFIX = 'Graduating PhDs in '
HREF_EMAIL_PREFIX = 'mailto:'
WEB_TEXT = 'home page'
EMAIL_PREFIX = 'Email:'

counts = {
    'dir': 0,
    'dir-email': 0,
    'phd': 0,
    'phd-email': 0,
}

def download(url, download_dir, page):
  output_file = '%s/page-%d.html' % (download_dir, page)
  return util.download(url, output_file, OVERWRITE_DOWNLOAD)

def validate_dir_header(tr):
  ths = tr.find_all('th')
  assert len(ths) == 6, 'expecting %d columns, got %d: %s' % (
      6, len(ths), tr)
  assert ths[0].get_text().strip() == 'Name'
  assert ths[1].get_text().strip() == 'Title'
  assert ths[2].get_text().strip() == 'Location'
  assert ths[3].get_text().strip() == 'Phone'
  assert ths[4].get_text().strip() == 'Email'
  assert ths[5].get_text().strip() == 'Mail'

def find_section(trs, section=None, start=0):
  for i in range(start, len(trs)):
    if 'bgcolor' not in trs[i].attrs or trs[i]['bgcolor'] != '#FFFF99':
      continue
    if section is None:
      return i
    text = trs[i].get_text().strip()
    if text == section:
      return i
  return -1

def process_dir(download_file):
  # To be lenient.  Html table is malformed.
  soup = BeautifulSoup(open(download_file), 'lxml')
  tables = soup.find_all('table', class_='searchTbl')
  assert len(tables) == 2, 'expecting %d tables, got %d: %s' % (
      2, len(tables), download_file)
  trs = tables[1].find_all('tr')
  assert len(trs) > 0
  validate_dir_header(trs[0])

  # Parse Researchers/Post-Docs/Visitors section.
  start = find_section(trs, section=DIR_SECTION) + 1
  assert start > 0, 'could not find section %s: %s' % (
      DIR_SECTION, download_file)
  end = find_section(trs, start=start)
  assert end > start, 'could not find end of section: %s' % download_file

  items = []
  for i in range(start, end):
    tds = trs[i].find_all('td')
    assert len(tds) == 6, 'expecting %d columns, got %d: %s' % (
        6, len(tds), trs[i])
    name = tds[0].get_text().strip()
    last, first = name.split(', ')
    name = '%s %s' % (first, last)
    email = tds[4].get_text().strip()
    assert email != ''
    a = tds[4].find_all('a')
    # TODO: handle multiple emails.
    if len(a) == 1:
      assert a[0]['href'] == 'mailto:%s' % email, (
          'expecting mailto:%s, got %s: %s' % (
              email, a[0]['href'], trs[i]))
    else:
      email = ''
    item = {'name': name, 'title': util.Title.STAFF}
    counts['dir'] += 1
    if email != '':
      item['email'] = email
      counts['dir-email'] += 1
    items.append(item)
  return items

def get_email(raw):
  parts = raw.strip().replace(u'\xa0', u' ').split(' ')  # &nbsp => space
  email = ''
  for part in parts:
    if part == 'at':
      part = '@'
    if part == 'dot':
      part = '.'
    email += part
  if validate_email(email):
    return email
  return None

def process_phd_content(raw_lines):
  lines = []
  for line in raw_lines:
    if line != u'\ufeff':
      lines.append(line)

  items = []
  index = 0
  while index < len(lines):
    # Name is first in a block.
    name = lines[index].strip().replace(u'\xa0', u' ')  # &nbsp => space
    num_parts = len(name.split(' '))
    if num_parts == 1:
      index += 1
      assert index < len(lines)
      last = lines[index].strip().replace(u'\xa0', u' ')  # &nbsp => space
      assert len(last.split(' ')) == 1, lines[index]
      name = '%s %s' % (name, last)
    else:
      assert num_parts >= 2 and num_parts <= 5, 'invalid name: %s' % name
    # Find email, which is last in a block.
    email = None
    index += 1
    while index < len(lines):
      p = lines[index].find('@')
      if p >= 0 and validate_email('x%s' % lines[index][p:]):
        if validate_email(lines[index]):
          email = lines[index]
        break
      if lines[index] == EMAIL_PREFIX:
        index += 1
        assert index < len(lines)
        raw = lines[index]
        # Extremely hacky.. in a few cases email address is split to two lines.
        if len(raw) < 12:
          index += 1
          assert index < len(lines)
          raw = '%s %s' % (raw, lines[index])
        assert len(raw) >= 12
        email = get_email(lines[index])
        break
      if lines[index].startswith(EMAIL_PREFIX):
        raw = lines[index][len(EMAIL_PREFIX):]
        # Extremely hacky.. in a few cases email address is split to two lines.
        if len(raw) < 12:
          index += 1
          assert index < len(lines)
          raw = '%s %s' % (raw, lines[index])
        assert len(raw) >= 12
        email = get_email(raw)
        break
      index += 1

    item = {'name': name, 'title': util.Title.PHD}
    counts['phd'] += 1
    if email is not None:
      item['email'] = email
      counts['phd-email'] += 1
    items.append(item)
    index += 1
  return items

def process_phd(download_file):
  soup = BeautifulSoup(open(download_file), 'html.parser')

  # Get graduating year.
  #h1 = soup.find_all('h1', class_='title')
  #assert len(h1) == 1, 'expecting %d title, found %d: %s' % (
  #    1, len(h1), download_file)
  #title = h1[0].get_text().strip()
  #assert title.startswith(PHD_TITLE_PREFIX), 'expecting %s in title: %s' % (
  #    PHD_TITLE_PREFIX, title)
  #year = title[len(PHD_TITLE_PREFIX):]
  #year, _ = year.split('-')
  #assert len(year) == 4 and int(year) > 2000 and int(year) < 2020, (
  #    'invalid year %s: %s' % (year, title))

  # Get content block.
  divs = soup.find_all('div', class_='content')
  assert len(divs) == 7, 'expecting %d content divs, got %d: %s' % (
      7, len(divs), download_file)
  items = process_phd_content([s for s in divs[2].stripped_strings])
  #for item in items:
  #  item['year'] = year

  return items

def process(download_file, key, processed_dir, page):
  output_file = '%s/page-%d.txt' % (processed_dir, page)
  if os.path.isfile(output_file) and not OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
  if key == 'dir':
    items = process_dir(download_file)
  elif key == 'phd':
    items = process_phd(download_file)
  else:
    assert False, 'unknown key: %s' % key
  with open(output_file, 'w') as fp:
    for item in items:
      print >> fp, item

def download_and_process(url, key, download_dir, processed_dir, page_counts):
  page_counts[key] += 1
  download_file = download(url, download_dir, page_counts[key])
  process(download_file, key, processed_dir, page_counts[key])

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--download_dir', required=True)
  parser.add_argument('--processed_dir', required=True)
  args = parser.parse_args()

  util.prepare_dirs(URL_SUBDIR_MAP, args.download_dir, args.processed_dir)
  page_counts = {subdir: 0 for subdir in set(URL_SUBDIR_MAP.values())}
  for url, subdir in URL_SUBDIR_MAP.iteritems():
    print 'processing %s => %s' % (url, subdir)
    download_dir = '%s/%s' % (args.download_dir, subdir)
    processed_dir = '%s/%s' % (args.processed_dir, subdir)
    download_and_process(url, subdir, download_dir, processed_dir, page_counts)
  print counts

if __name__ == '__main__':
  main()

