#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'https://www.cics.umass.edu/people/graduate-students': 'grad',
    ('https://www.cics.umass.edu/people/graduating_phds'
     '?field_graduation_year_value=All&page='): 'phd',
    ('https://www.cics.umass.edu/people/graduating_ms'
     '?field_graduation_year_value=All&page='): 'master',
}

PAGE_MAP = {
    'grad': None,
    'phd': 8,
    'master': 3
}

counts = {
    'grad': 0,
    'phd': 0,
    'master': 0,
}

def download(url, download_dir):
  output_file = '%s/page-1.html' % download_dir
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def download_page(url, page, download_dir):
  output_file = '%s/page-%d.html' % (download_dir, page+1)
  return util.download('%s%d' % (url, page), output_file, util.OVERWRITE_DOWNLOAD)

def get_name(text):
  if text.find(',') < 0:
    return text
  last, first = text.split(', ')
  return '%s %s' % (first, last)

def process_grad(soup):
  tables = soup.find_all('table')
  assert len(tables) == 1
  trs = tables[0].find_all('tr')
  ths = trs[0].find_all('th')
  assert [th.get_text().strip() for th in ths] == [
      'Name', 'Phone', 'E-Mail (@cs.umass.edu)']
  items = []
  for i in range(1, len(trs)):
    ths = trs[i].find_all('th')
    assert len(ths) == 3, trs[i]
    name = get_name(ths[0].get_text().strip())
    assert name != ''
    user = ths[2].get_text().strip()
    email = ''
    if user != '':
      email = '%s@cs.umass.edu' % user
    item = {'name': name, 'title': util.Title.GRAD}
    if email != '':
      item['email'] = email
    items.append(item)
    counts['grad'] += 1
  return items

EMAIL_PREFIX = 'mailto:'
def get_email(a):
  email = ''
  for aa in a:
    if aa['href'].startswith(EMAIL_PREFIX):
      assert email == ''
      email = aa['href'][len(EMAIL_PREFIX):].strip()
  return email

def process_phd_master(soup, title):
  divs = soup.find_all('div', class_='group-person-info-panel')
  items = []
  for div in divs:
    h2s = div.find_all('h2')
    assert len(h2s) == 1, div
    name = get_name(h2s[0].get_text().strip())
    email = get_email(div.find_all('a'))
    item = {'name': name, 'title': title}
    if email != '':
      item['email'] = email
    items.append(item)
    counts[title] += 1
  return items

def process(download_file, key, processed_dir):
  p = download_file.rfind('/')
  q = download_file.rfind('.')
  output_file = '%s/%s.txt' % (processed_dir, download_file[p+1:q])
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file
  soup = BeautifulSoup(open(download_file), 'html.parser')
  if key == 'grad':
    items = process_grad(soup)
  elif key == 'phd':
    items = process_phd_master(soup, util.Title.PHD)
  else:
    assert key == 'master', key
    items = process_phd_master(soup, util.Title.MASTER)
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

  print '================================================================'
  print 'WARNING: update page counts for graduating phd/master students!!'
  print '================================================================'

  util.prepare_dirs(URL_SUBDIR_MAP, args.download_dir, args.processed_dir)
  for url, subdir in URL_SUBDIR_MAP.iteritems():
    print 'processing %s => %s' % (url, subdir)
    download_dir = '%s/%s' % (args.download_dir, subdir)
    processed_dir = '%s/%s' % (args.processed_dir, subdir)
    pages = PAGE_MAP[subdir]
    if pages is None:
      download_file = download(url, download_dir)
      process(download_file, subdir, processed_dir)
    else:
      for i in range(pages):
        download_file = download_page(url, i, download_dir)
        process(download_file, subdir, processed_dir)
  print counts

if __name__ == '__main__':
  main()

