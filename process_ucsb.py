#!/usr/bin/python

from bs4 import BeautifulSoup
from validate_email import validate_email

import argparse
import os
import util

# Url to subdir mapping.
URL_SUBDIR_MAP = {
    'https://www.cs.ucsb.edu/people/grad': util.Title.GRAD,
    'https://www.cs.ucsb.edu/people/alumni': util.Title.GRAD_ALUMNI,
}

counts = {
    util.Title.UNDERGRAD: 0,
    util.Title.MASTER: 0,
    util.Title.PHD: 0,
    util.Title.UNDERGRAD_ALUMNI: 0,
    util.Title.MASTER_ALUMNI: 0,
    util.Title.PHD_ALUMNI: 0,
}

def download(url, download_dir):
  output_file = '%s/page-1.html' % download_dir
  return util.download(url, output_file, util.OVERWRITE_DOWNLOAD)

def parse_table(download_file):
  soup = BeautifulSoup(open(download_file), 'html.parser')
  tables = soup.find_all('table', class_='views-table cols-6')
  assert len(tables) == 1, 'expecting %d tables, found %d: %s' % (
      1, len(tables), download_file)
  trs = tables[0].find_all('tr')
  assert len(trs) > 0
  ths = trs[0].find_all('th')
  header = [th.get_text().strip() for th in ths]
  rows = []
  for i in range(1, len(trs)):
    rows.append(trs[i].find_all('td'))
  return header, rows

def get_title(position, is_alumni):
  if is_alumni:
    items = set([item.strip() for item in position.split(',')])
    if 'Ph.D.' in items:
      return util.Title.PHD_ALUMNI
    if 'M.S.' in items:
      return util.Title.MASTER_ALUMNI
    if 'B.S.' in items:
      return util.Title.UNDERGRAD_ALUMNI
    assert False, position
  if position == 'Ph.D.':
    return util.Title.PHD
  if position == 'M.S.':
    return util.Title.MASTER
  if position == 'B.S.':
    return util.Title.UNDERGRAD
  assert False, position

def process_grad(download_file):
  header, rows = parse_table(download_file)
  assert header == [
      'Name',
      'Academic Level',
      'Phone',
      'Email',
      'Office',
      'Website'], 'unexpected header: %s' % header
  items = []
  for row in rows:
    assert len(row) == len(header), 'bad row: %s' % row
    name = row[0].get_text().strip()
    assert name != ''
    title = get_title(row[1].get_text().strip(), False)
    email = row[3].get_text().strip()
    if not validate_email(email):
      email = ''
    item = {'name': name, 'title': title}
    counts[title] += 1
    if email != '':
      item['email'] = email
    items.append(item)
  return items

def process_alumni(download_file):
  header, rows = parse_table(download_file)
  assert header == [
      'Name',
      'Degree',
      'Phone',
      'Email',
      'Employer',
      'Website'], 'unexpected header: %s' % header
  items = []
  for row in rows:
    assert len(row) == len(header), 'bad row: %s' % row
    name = row[0].get_text().strip()
    assert name != ''
    title = get_title(row[1].get_text().strip(), True)
    email = row[3].get_text().strip()
    if not validate_email(email):
      email = ''
    item = {'name': name, 'title': title}
    counts[title] += 1
    if email != '':
      item['email'] = email
    items.append(item)
  return items

def process(download_file, key, processed_dir):
  output_file = '%s/page-1.txt' % processed_dir
  if os.path.isfile(output_file) and not util.OVERWRITE_PROCESSED:
    print '%s exists and not overwritable' % output_file
    return output_file
  if key == util.Title.GRAD:
    items = process_grad(download_file)
  elif key == util.Title.GRAD_ALUMNI:
    items = process_alumni(download_file)
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

