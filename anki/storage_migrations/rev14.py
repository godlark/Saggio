def upgrade_to_rev14(col):
    col.db.executescript("""
    PRAGMA foreign_keys=off;

    BEGIN TRANSACTION;

    ALTER TABLE revlog RENAME TO _revlog_old;

    create table if not exists revlog (
        id              integer primary key,
        cid             integer not null,
        usn             integer not null,
        ease            integer not null,   
        ivl             decimal not null,
        lastIvl         decimal not null,
        factor          integer not null,
        time            integer not null,
        type            integer not null,
        due             integer not null,
        day             integer not null
    );

    INSERT INTO revlog (id, cid, usn, ease, ivl, lastIvl, factor, time, type, due, day)
    SELECT id, cid, usn, ease, ivl, lastIvl, factor, time, type, -1, -1
    FROM _revlog_old;

    COMMIT;

    PRAGMA foreign_keys=on;
                """)
    col.db.execute('DROP TABLE IF EXISTS _revlog_old')
    col.db.execute("update col set ver = 14")