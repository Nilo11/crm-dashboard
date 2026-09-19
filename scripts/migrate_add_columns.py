import sqlite3
DB='crm_database.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute("PRAGMA table_info(leads)")
cols=[r[1] for r in cur.fetchall()]
print('Existing columns:', cols)
if 'value' not in cols:
    print('Adding value column')
    cur.execute("ALTER TABLE leads ADD COLUMN value REAL DEFAULT 0")
if 'notes' not in cols:
    print('Adding notes column')
    cur.execute("ALTER TABLE leads ADD COLUMN notes TEXT")
conn.commit()
conn.close()
print('Done')
