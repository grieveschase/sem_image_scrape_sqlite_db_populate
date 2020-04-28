import datetime
from datetime import datetime
import sqlite3
from datetime import timedelta
import sys
import os

try:
    remove_days = int(sys.argv[1])
except ValueError:
    print("\nFirst arg must be integer for age of files to remove.")
    print("\nExiting script, no changes made to DBs")
    sys.exit(1)

main_db = (os.getenv('main_db_path') or sys.argv[2])
if not os.path.isfile(main_db):
    print("\nprovided main db file path does not exist!")
    print("\nProvided path: " + main_db)
    print("\nExiting script, no changes made to DBs")
    sys.exit(1)

backup_db = (os.getenv('backup_db_path') or sys.argv[3])
if not os.path.isfile(main_db):
    print("\nprovided backup db file path does not exist!")
    print("\nProvided path: " + backup_db)
    print("\nExiting script, no changes made to DBs")
    sys.exit(1)

print("\n"+main_db)
print("\n"+backup_db)
print("\n"+str(remove_days))

try:
    conn = sqlite3.connect(main_db)
    cur = conn.cursor()
    sql_input_delete = "DELETE FROM patternfov WHERE DATE < '" + (datetime.now() -  timedelta(days = remove_days)).strftime("%Y-%m-%d %H:%M:%S") + "'"
    cur.execute(sql_input_delete)
    conn.commit()
    print("patternfov Successfully deleted main_db")

    sql_input_delete = "DELETE FROM measdisplay_obs WHERE DATE < '" + (datetime.now() -  timedelta(days = remove_days)).strftime("%Y-%m-%d %H:%M:%S") + "'"
    cur.execute(sql_input_delete)
    conn.commit()
    print("measdisplay_obs Successfully deleted main_db")
    cur.close()
    conn.close()
    print('Successfully Deleted images older than %s days from main db!\n'%str(remove_days))

except sqlite3.Error as error:
    print("Error when deleting images from main db: ", error)
    print("Exiting Script after main_db delete error")
    if (conn):
        sys.exit(1)
finally:
    if (conn):
        conn.close()

try:
    conn = sqlite3.connect(backup_db)
    cur = conn.cursor()
    sql_input_delete = "DELETE FROM patternfov WHERE DATE < '" + (datetime.now() -  timedelta(days = remove_days)).strftime("%Y-%m-%d %H:%M:%S") + "'"
    cur.execute(sql_input_delete)
    conn.commit()
    print("patternfov Successfully deleted backup db")

    sql_input_delete = "DELETE FROM measdisplay_obs WHERE DATE < '" + (datetime.now() -  timedelta(days = remove_days)).strftime("%Y-%m-%d %H:%M:%S") + "'"
    cur.execute(sql_input_delete)
    conn.commit()
    print("measdisplay_obs Successfully deleted back up")
    cur.close()
    conn.close()
    print('Successfully Deleted images older than %s days from backup db!'%str(remove_days))

except sqlite3.Error as error:
    print("Error when deleting images from backup db: ", error)


finally:
    if (conn):
        conn.close()










#
