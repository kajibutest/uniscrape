#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'http://www.cms.caltech.edu/people/grad': 'grad',
    'http://www.cms.caltech.edu/people/postdocs': 'postdoc',
    'http://www.cms.caltech.edu/contact/directory': 'dir',
}

# None means not interested.  It will be skipped.
POSITION_TITLE_MAP = {
    'administrative staff': None,
    'emeriti faculty': None,
    'faculty': None,
    'graduate student': util.Title.GRAD,
    'lecturer': util.Title.STAFF,
    'postdoctoral scholar': util.Title.POSTDOC,
    'research faculty': None,
    'research staff': util.Title.STAFF,
    'technical staff': util.Title.STAFF,
    'undergraduate student': util.Title.UNDERGRAD,
    'visiting faculty': None,
    'visitor': util.Title.STAFF,
}

HOME_PREFIX = 'http://directory.caltech.edu/cgi-bin/search.cgi?uid='

GRAD_DIV_CLASS = 'dynamic-2col no-height'
POSTDOC_UL_CLASS = 'no-list-style'
DIR_TABLE_CLASS = 'table1'

counts = {
    'total': 0,
    'grad': 0,
    'postdoc': 0,
    'dir': 0,
}

def download(url, download_dir):
  output_file = '%s/page-1.html' % download_dir
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def get_email(a):
  href = a['href'].strip()
  assert href.startswith(HOME_PREFIX)
  email = '%s@caltech.edu' % href[len(HOME_PREFIX):]
  assert validate_email(email), 'invalid email: %s' % email
  return email

def process_grad(download_file):
  soup = BeautifulSoup(open(download_file), 'html.parser')
  divs = soup.find_all('div', class_=GRAD_DIV_CLASS)
  assert len(divs) == 1, 'found %d divs of class "%s"' % (
      len(divs), GRAD_DIV_CLASS)
  lis = divs[0].find_all('li')
  items = []
  for li in lis:
    name = li.get_text().strip()
    assert name != '', 'empty name in %s' % li
    a = li.find_all('a')
    assert len(a) == 1, 'found %d link in %s' % (len(a), li)
    email = get_email(a[0])
    items.append({'name': name, 'email': email, 'title': util.Title.GRAD})
    counts['total'] += 1
    counts['grad'] += 1
  return items

def process_postdoc(download_file):
  soup = BeautifulSoup(open(download_file), 'html.parser')
  uls = soup.find_all('ul', class_=POSTDOC_UL_CLASS)
  assert len(uls) == 1, 'found %d uls of class "%s"' % (
      len(uls), POSTDOC_UL_CLASS)
  lis = uls[0].find_all('li')
  items = []
  for li in lis:
    a = li.find_all('a')
    assert len(a) == 1, 'found %d link in %s' % (len(a), li)
    name = a[0].get_text().strip()
    assert name != '', 'empty name in %s' % li
    email = get_email(a[0])
    items.append({'name': name, 'email': email, 'title': util.Title.POSTDOC})
    counts['total'] += 1
    counts['postdoc'] += 1
  return items

def get_title(position):
  position = position.lower()
  assert position in POSITION_TITLE_MAP, position
  return POSITION_TITLE_MAP[position]

def process_dir(download_file):
  soup = BeautifulSoup(open(download_file), 'html.parser')
  tables = soup.find_all('table', class_=DIR_TABLE_CLASS)
  assert len(tables) == 1, 'found %d tables of class "%s"' % (
      len(tables), DIR_TABLE_CLASS)
  trs = tables[0].find_all('tr')
  assert len(trs) > 0
  ths = trs[0].find_all('th')
  # Name, position, office, ext, email (image).
  assert len(ths) == 5, 'expecting %d th, found %d' % (5, len(ths))
  items = []
  for i in range(1, len(trs)):
    tds = trs[i].find_all('td')
    assert len(tds) == 5, 'failed to parse %s' % trs[i]
    name = tds[0].get_text().strip()
    last, first = name.split(', ')
    name = '%s %s' % (first, last)
    a = tds[0].find_all('a')
    assert len(a) == 1, 'found %d link in %s' % (len(a), td)
    email = get_email(a[0])
    title = get_title(tds[1].get_text().strip())
    if title is None:
      continue
    item = {'name': name, 'email': email, 'title': title}
    counts['total'] += 1
    counts['dir'] += 1
    items.append(item)
  return items

def process(download_file, key, processed_dir):
  output_file = '%s/page-1.txt' % processed_dir
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file
  if key == 'grad':
    items = process_grad(download_file)
  elif key == 'postdoc':
    items = process_postdoc(download_file)
  elif key == 'dir':
    items = process_dir(download_file)
  else:
    assert False, 'unrecognized key: %s' % key
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

