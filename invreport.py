from invutils import PasswordLoader, JHLoader, PAILoader, SheetLoader, FidelityLoader
import yaml
import json
import sys

if len(sys.argv) == 1:
    print "Usage: invreport /path/to/config/file"
else:
    try:
        with open(sys.argv[1], 'r') as f:
            cfg = yaml.load(f)
    except Exception, e:
        print "Couldn't load " + sys.argv[1]
        print "Error: " + str(e)
