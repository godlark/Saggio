def upgrade_to_rev13(col):
    try:
        col.load()
        col.conf['usedScheduler'] = 'anki.sched.Scheduler' if (col.conf['schedVer'] == 1) else 'anki.schedv2.Scheduler'
        col.setMod()
        col.save()
        col.db.execute("update col set ver = 13")
    except Exception as e:
        print(e)