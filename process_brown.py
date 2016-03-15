#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'https://cs.brown.edu/people/grad/': 'grad',
    'https://cs.brown.edu/people/ugrad/': 'undergrad',
    'https://cs.brown.edu/people/directory/': 'dir',
}

GRAD_ID_TITLE_MAP = {
    'doctoral-students': util.Title.PHD,
    'masters-students': util.Title.MASTER,
}

GRAD_TITLE_TEXT_MAP = {
    util.Title.PHD: 'Doctoral Student',
    util.Title.MASTER: 'Masters Student',
}

GRAD_LINK_PREFIX = '/people/grad/'
GRAD_LINK_SUFFIX = '/'

UNDERGRAD_LINK_PREFIX = '/people/ugrad/'
UNDERGRAD_LINK_SUFFIX = '/'

DIR_TEXT_TITLE_MAP = {
    'PhD Student': util.Title.PHD,
    'Masters Student': util.Title.MASTER,
    'Technical Staff': util.Title.STAFF,
    'Postdoc': util.Title.POSTDOC,
    'Research Staff': util.Title.STAFF,
    'Visitor': util.Title.STAFF,
}

counts = {
    'phd': 0,
    'master': 0,
    'undergrad': 0,
    'staff': 0,
    'postdoc': 0,
}

def download(url, download_dir):
  output_file = '%s/page-1.html' % download_dir
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def get_email(a, prefix, suffix):
  email = None
  for aa in a:
    if aa['href'].startswith(prefix):
      assert aa['href'].endswith(suffix), a
      assert email is None, a
      email = '%s@brown.edu' % aa['href'][len(prefix):-len(suffix)]
  assert email is not None, a
  return email

def process_grad(soup):
  h2s = soup.find_all('h2')
  items = []
  for h2 in h2s:
    if 'id' not in h2.attrs:
      continue
    title = GRAD_ID_TITLE_MAP[h2.attrs['id']]
    ul = h2.findNextSibling('ul', class_='profile-list')
    uls = ul.find_all('ul')
    for ul in uls:
      name_li = ul.find_all('li', class_='profile-name')
      assert len(name_li) == 1, li
      name = name_li[0].get_text().strip()
      assert name != ''
      title_li = ul.find_all('li', class_='profile-title')
      assert len(title_li) == 1, li
      assert title_li[0].get_text().strip() == GRAD_TITLE_TEXT_MAP[title]
      link_li = ul.find_all('li', class_='profile-link')
      assert len(link_li) == 1, li
      a = link_li[0].find_all('a')
      email = get_email(
          link_li[0].find_all('a'), GRAD_LINK_PREFIX, GRAD_LINK_SUFFIX)
      items.append({'name': name, 'title': title, 'email': email})
      counts[title] += 1
  return items

def process_undergrad(soup):
  uls = soup.find_all('ul', class_='profile-list profile-compact')
  assert len(uls) == 1
  uls = uls[0].find_all('ul')
  items = []
  for ul in uls:
    name_li = ul.find_all('li', class_='profile-name')
    assert len(name_li) == 1, li
    name = name_li[0].get_text().strip()
    assert name != ''
    link_li = ul.find_all('li', class_='profile-link')
    assert len(link_li) == 1, li
    email = get_email(
        link_li[0].find_all('a'), UNDERGRAD_LINK_PREFIX, UNDERGRAD_LINK_SUFFIX)
    items.append({'name': name, 'title': util.Title.UNDERGRAD, 'email': email})
    counts['undergrad'] += 1
  return items

def get_dir_title(td):
  return DIR_TEXT_TITLE_MAP.get(td.get_text().strip(), None)

def process_dir(soup):
  tables = soup.find_all('table', id='deptdir')
  assert len(tables) == 1
  trs = tables[0].find_all('tr')
  # Check header.
  ths = trs[0].find_all('th')
  assert [th.get_text().strip() for th in ths] == [
      'Name', 'Office', 'Phone', 'Status', 'Email', 'Assistant']
  items = []
  for i in range(1, len(trs)):
    tds = trs[i].find_all('td')
    title = get_dir_title(tds[3])
    if title is None:
      continue
    name = tds[0].get_text().strip()
    last, first = name.split(', ')
    name = '%s %s' % (first, last)
    assert name != ''
    user = tds[4].get_text().strip()
    if user != '':
      email = '%s@brown.edu' % user
    items.append({'name': name, 'title': title, 'email': email})
    counts[title] += 1
  return items

def process(download_file, key, processed_dir):
  output_file = '%s/page-1.txt' % processed_dir
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file
  soup = BeautifulSoup(open(download_file), 'html.parser')
  if key == 'grad':
    items = process_grad(soup)
  elif key == 'undergrad':
    items = process_undergrad(soup)
  else:
    assert key == 'dir', key
    items = process_dir(soup)
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

