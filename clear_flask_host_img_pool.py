import os
import datetime
flask_img_pool_path = "C://Python3//flask_host//app//static//FOV//"

img_dirs = [flask_img_pool_path+i for i in os.listdir(flask_img_pool_path)]
dir_time_stamp = lambda x: datetime.datetime.fromtimestamp(os.stat(x).st_mtime)
dir_age_sec = lambda x: (datetime.datetime.today() - dir_time_stamp(x)).total_seconds()

seconds_lookback = 60 * 30

old_img_files = list(filter((lambda x: dir_age_sec(x) > seconds_lookback), img_dirs))

for i in old_img_files:
	os.remove(i)
	
