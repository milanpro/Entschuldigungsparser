#IMAP_port: 143
#Mail: test@pohlers-web.de
#name: m02c0434
#pass: milanfelix42
#server: w0089225.kasserver.com

import imaplib, getpass

M = imaplib.IMAP4()
M.login(getpass.getuser(), getpass.getpass())
M.select()
typ, data = M.search(None, 'ALL')
for num in data[0].split():
    typ, data = M.fetch(num, '(RFC822)')
    print 'Message %s\n%s\n' % (num, data[0][1])
M.close()
M.logout()
