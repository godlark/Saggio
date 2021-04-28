def upgrade_to_rev12(col):
    try:
        col.db.execute('select ivl_dec from cards limit 1')
        col.db.executescript("""
PRAGMA foreign_keys=off;
            
BEGIN TRANSACTION;

ALTER TABLE cards RENAME TO _cards_old;

create table if not exists cards (
    id              integer primary key,   /* 0 */
    nid             integer not null,      /* 1 */
    did             integer not null,      /* 2 */
    ord             integer not null,      /* 3 */
    mod             integer not null,      /* 4 */
    usn             integer not null,      /* 5 */
    type            integer not null,      /* 6 */
    queue           integer not null,      /* 7 */
    due             integer not null,      /* 8 */
    ivl             decimal not null,      /* 9 */
    factor          integer not null,      /* 10 */
    reps            integer not null,      /* 11 */
    lapses          integer not null,      /* 12 */
    left            integer not null,      /* 13 */
    odue            integer not null,      /* 14 */
    odid            integer not null,      /* 15 */
    flags           integer not null,      /* 16 */
    data            text not null          /* 17 */
);

INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)
SELECT id, nid, did, ord, mod, usn, type, queue, due, ivl_dec, factor, reps, lapses, left, odue, odid, flags, data
FROM _cards_old;

COMMIT;

PRAGMA foreign_keys=on;
            """)
        col.db.execute('DROP TABLE IF EXISTS _cards_old')
    except:
        col.db.executescript("""
PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

ALTER TABLE cards RENAME TO _cards_old;

create table if not exists cards (
    id              integer primary key,   /* 0 */
    nid             integer not null,      /* 1 */
    did             integer not null,      /* 2 */
    ord             integer not null,      /* 3 */
    mod             integer not null,      /* 4 */
    usn             integer not null,      /* 5 */
    type            integer not null,      /* 6 */
    queue           integer not null,      /* 7 */
    due             integer not null,      /* 8 */
    ivl             decimal not null,      /* 9 */
    factor          integer not null,      /* 10 */
    reps            integer not null,      /* 11 */
    lapses          integer not null,      /* 12 */
    left            integer not null,      /* 13 */
    odue            integer not null,      /* 14 */
    odid            integer not null,      /* 15 */
    flags           integer not null,      /* 16 */
    data            text not null          /* 17 */
);

INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)
SELECT id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data
FROM _cards_old;

COMMIT;

PRAGMA foreign_keys=on;
                        """)
        col.db.execute('DROP TABLE IF EXISTS _cards_old')
    finally:
        col.db.execute("update col set ver = 12")