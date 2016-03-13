#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import phonenumbers
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'https://www.scs.cmu.edu/directory/all?term_node_tid_depth=All&page=': 'all'
}

# None means not interested.
POSITION_TITLE_LIST = [
    [['professor', 'administrat'], None],
    [['teaching assistant',
      'research assistant',
      'graduate student'],
     util.Title.GRAD],
    [['ms student'], util.Title.MASTER],
    [['postdoc'], util.Title.POSTDOC],
    [['intern',
      'visitor',
      'visiting',
      'programmer',
      'developer',
      'instructor',
      'engineer',
      'researcher',
      'scientist',
      'lecturer',
      'technician',
      'research associate'],
      util.Title.STAFF],
]

MIN_PAGE = 0
MAX_PAGE = 36
# Download page 0 to page-1.html etc, to be consistent with other schools.
OFFSET = 1

counts = {
    'total': 0,
    'email': 0,
}

def download(url, page, output_dir):
  url = '%s%d' % (url, page)
  output_file = '%s/page-%d.html' % (output_dir, page + OFFSET)
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def get_title(position):
  position = position.lower()
  for labels, title in POSITION_TITLE_LIST:
    is_title = False
    for label in labels:
      if position.find(label) >= 0:
        is_title = True
        break
    if is_title:
      return title
  # Not interested if position is not in existing map.
  return None

def process(afile, output_dir):
  p = afile.rfind('/') + 1
  assert p > 0
  q = afile.rfind('.')
  assert q > p
  output_file = '%s/%s.txt' % (output_dir, afile[p:q])
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file

  soup = BeautifulSoup(open(afile), 'html.parser')
  tables = soup.find_all('table', class_='views-table cols-6')
  assert len(tables) == 1, 'expecting %d tables, got %d: %s' % (
      1, len(tables), afile)
  trs = tables[0].find_all('tr')
  assert len(trs) > 0

  ths = trs[0].find_all('th')
  header = [th.get_text().strip() for th in ths]
  assert header == ['Last', 'First', 'Title', 'Office', 'Email', 'Phone']

  items = []
  for i in range(1, len(trs)):
    tds = trs[i].find_all('td')
    assert len(tds) == len(header)

    last = tds[0].get_text().strip()
    assert last != ''
    first = tds[1].get_text().strip()
    assert first != ''
    name = '%s %s' % (first, last)
    title = get_title(tds[2].get_text().strip())
    if title is None:
      continue

    user, domain = '', ''
    uspans = tds[4].find_all('span', class_='u')
    if len(uspans) > 0:
      assert len(uspans) == 1, tds[4]
      user = uspans[0].get_text().strip()
    dspans = tds[4].find_all('span', class_='d')
    if len(dspans) > 0:
      assert len(dspans) == 1, tds[4]
      domain = dspans[0].get_text().strip()
    assert (user == '') == (domain == ''), tds[4]

    item = {'name': name, 'title': title}
    counts['total'] += 1
    if user != '':
      item['email'] = '%s@%s' % (user, domain)
      counts['email'] += 1
    items.append(item)

  with open(output_file, 'w') as fp:
    for item in items:
      print >> fp, item

def download_and_process(url, page, download_dir, processed_dir):
  downloaded_file = download(url, page, download_dir)
  processed_file = process(downloaded_file, processed_dir)
  return [downloaded_file, processed_file]

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--download_dir', required=True)
  parser.add_argument('--processed_dir', required=True)
  args = parser.parse_args()

  print '=================================================='
  print 'WARNING: update MIN_PAGE and MAX_PAGE upon rerun!!'
  print '=================================================='

  util.prepare_dirs(URL_SUBDIR_MAP, args.download_dir, args.processed_dir)
  for url, subdir in URL_SUBDIR_MAP.iteritems():
    download_dir = '%s/%s' % (args.download_dir, subdir)
    processed_dir = '%s/%s' % (args.processed_dir, subdir)
    page = MIN_PAGE
    while page <= MAX_PAGE:
      download_and_process(url, page, download_dir, processed_dir)
      page += 1
  print counts

if __name__ == '__main__':
  main()

