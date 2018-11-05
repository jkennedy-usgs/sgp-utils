import SbSession
sb = SbSession.SbSession()
username = raw_input("Username:  ")
sb.loginc(str(username))
gda_key = '56e301cae4b0f59b85d3a346'
studyarea_keys = sb.get_child_ids(gda_key)
del1 = []
for k in studyarea_keys:
    del1.append(k)
    site_keys = sb.get_child_ids(k)
    del2 = []
    for s in site_keys:
        del2.append(s)
    sb.delete_items(del2)
sb.delete_items(del1)