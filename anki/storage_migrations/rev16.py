def upgrade_to_rev16(col):
    col.modSchema(check=False)
    for m in col.models.all():
        for template in m['tmpls']:
            template['note_type_id'] = 0
        col.models.save(m)
    col.db.execute("update col set ver = 16")