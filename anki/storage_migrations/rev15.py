def upgrade_to_rev15(col):
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
        data            text not null,         /* 17 */
        review_start_time   integer            /* 18 */
    );

    INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data, review_start_time)
    SELECT id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data, null as review_start_time
    FROM _cards_old;

    COMMIT;

    PRAGMA foreign_keys=on;
    """)
    col.db.execute('DROP TABLE IF EXISTS _cards_old')
    col.db.execute("update col set ver = 15")
