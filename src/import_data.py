import datetime
import json
import urllib
import time
import hashlib

import db


def main():
    url = 'http://fortunki.archlinux.pl/exportuj/json/date'
    resource = urllib.urlopen(url)
    data = json.loads(resource.read(), encoding='utf-8')
    import_userid = 'import:{0}'.format(int(time.time()))
    with db.database.transaction():
        for i, raw in enumerate(data):
            created = datetime.datetime.strptime(raw['added_date'],
                    '%Y-%m-%d %H:%M:%S.%f')
            id = hashlib.md5(raw['content'].encode('utf-8')).hexdigest()
            entry = db.Entry.create(content=raw['content'],
                    votes_count=raw['votes'], created=created, id=id)
            for _ in xrange(int(raw['votes'])):
                db.Vote.create(entry=entry, created=created,
                        userid=import_userid)
    print "Imported: {0}".format(len(data))

if __name__ == '__main__':
    main()
