import json


def upgrade_to_rev17(col):
    dconf = json.loads(col.db.first("""select dconf from col""")[0])
    for conf_id in dconf.keys():
        dconf[conf_id]['new']['initialFactors'] = {}
    print(dconf)
    col.db.execute("update col set dconf=?", json.dumps(dconf))
    col.db.execute("update col set ver = 17")