def parse_mail(text):
    mailtext = text.split("\n")
    _, name = mailtext[0].split("_",1)
    _, vorname = mailtext[1].split("_",1)
    _, grund = mailtext[2].split("_",1)
    print mailtext
    print name
    print vorname
    print grund
parse_mail("name_Proell\nvorname_Milan\nGrund_Testgrund")

    
