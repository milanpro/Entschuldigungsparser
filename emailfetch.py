#IMAP_port: 143
#Mail: *******
#name: *******
#pass: ********
#server: *******

import imaplib

#siehe e-learning

host.select()
typ, data = host.search(None, '(ALL)')
print typ, data, data[0].split()
for num in data[0].split():
    typ, data = host.fetch(num, '(BODY[TEXT])')
    print data[0][1]
host.close()
host.logout()
