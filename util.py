import os
import time

OVERWRITE_DOWNLOAD = False
OVERWRITE_PROCESSED = True

# Standardized titles:
# - undergrad (+alumni)
# - grad (+alumni)
#   - master (+alumni)
#   - phd (+alumni)
# - postdoc (+alumni)
# - staff (researcher etc.) -- does not include admin staff
class Title:
  UNDERGRAD = 'undergrad'
  GRAD = 'grad'
  MASTER = 'master'
  PHD = 'phd'
  POSTDOC = 'postdoc'
  STAFF = 'staff'
  ALUMNI = 'alumni'
  UNDERGRAD_ALUMNI = '%s-%s' % (UNDERGRAD, ALUMNI)
  GRAD_ALUMNI = '%s-%s' % (GRAD, ALUMNI)
  MASTER_ALUMNI = '%s-%s' % (MASTER, ALUMNI)
  PHD_ALUMNI = '%s-%s' % (PHD, ALUMNI)
  POSTDOC_ALUMNI = '%s-%s' % (POSTDOC, ALUMNI)
  STAFF_ALUMNI = '%s-%s' % (STAFF, ALUMNI)
  OTHER = 'other'

  ALL = [UNDERGRAD, GRAD, MASTER, PHD, POSTDOC, STAFF,
         ALUMNI, UNDERGRAD_ALUMNI, GRAD_ALUMNI, MASTER_ALUMNI,
         PHD_ALUMNI, POSTDOC_ALUMNI, STAFF_ALUMNI, OTHER]

############
# IO utils #
############

def prepare_dirs(url_subdir_map, download_dir, processed_dir):
  for adir in (download_dir, processed_dir):
    if not os.path.isdir(adir):
      os.makedirs(adir)
    for subdir in url_subdir_map.itervalues():
      sdir = '%s/%s'% (adir, subdir)
      if not os.path.isdir(sdir):
        os.makedirs(sdir)

################
# System utils #
################

WGET = '/usr/local/bin/wget'
SLEEP_SECS = 1

def wait(secs=SLEEP_SECS):
  print 'sleeping for %d secs' % secs
  time.sleep(secs)

def download(url, output_file, overwrite):
  if os.path.isfile(output_file) and not overwrite:
    print '%s exists and not overwritable' % output_file
    return output_file
  wait()
  cmd = '%s "%s" -O %s -q' % (WGET, url, output_file)
  print 'running command: %s' % cmd
  assert os.system(cmd) == 0
  return output_file

