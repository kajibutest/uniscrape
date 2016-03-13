#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'http://www.cs.columbia.edu/people/directory': 'all',
}

POSITION_TITLE_MAP = {
    'faculty': None,
    'adjunct': None,
    'admin-staff': None,
    'tech-staff': util.Title.STAFF,
    'research-staff': util.Title.STAFF,
    'postdoc': util.Title.POSTDOC,
    'research-scientist': util.Title.STAFF,
    'PhD_student': util.Title.PHD,
    'DES_student': util.Title.GRAD,
    'MS_student': util.Title.MASTER,
}

JS_PREFIX = 'hideemail('

counts = {t: 0 for t in util.Title.ALL}
for t in util.Title.ALL:
  counts['%s-email' % t] = 0

def download(url, download_dir):
  output_file = '%s/page-1.html' % download_dir
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def process(download_file, processed_dir):
  output_file = '%s/page-1.txt' % processed_dir
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file
  soup = BeautifulSoup(open(download_file), 'html.parser')

  items = []
  a = soup.find_all('a')
  for aa in a:
    if 'name' not in aa.attrs:
      continue
    title = POSITION_TITLE_MAP.get(aa['name'], None)
    if title is None:
      continue
    table = aa.findNextSibling('table')
    trs = table.find_all('tr')
    for tr in trs:
      tds = tr.find_all('td')
      assert len(tds) == 4, tr
      name = tds[0].get_text().strip()
      last, first = name.split(', ')
      name = '%s %s' % (first, last)
      email = ''
      js = tds[2].find_all('script')
      if len(js) > 0:
        assert len(js) == 1, tr
        js = js[0].get_text().strip()
        assert js.startswith(JS_PREFIX)
        _, user, domain, _, _ = js.split(',')
        user = user.strip(" '\"")
        domain = domain.strip(" '\"")
        if user != '' and domain != '':
          email = '%s@%s' % (user, domain)
      item = {'name': name, 'title': title}
      counts[title] += 1
      if email != '':
        item['email'] = email
        counts['%s-email' % title] += 1
      items.append(item)
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

