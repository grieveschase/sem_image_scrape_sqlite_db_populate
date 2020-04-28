import os
import datetime
import sqlite3
import numpy as np
import cv2
import io
from io import BytesIO
from PIL import Image
import sys

'''
input
vsem_dir: file path to image directory on the SEM.
		ie: vsem_dir = "home//ccag//Desktop//Vera402//images//AutoSave//Production//Production//VSEM402//"
seconds_lookback: max age of directory to bring back.
obs_folder_name: Which folder, MeasDisplay for OBS images, PatternFov.
	-only returns folders that contain that folder.
'''
def sem_img_gather_folders(vsem_dir, seconds_lookback, obs_folder_name):
	# vsem_dir = "home//ccag//Desktop//Vera402//images//AutoSave//Production//Production//VSEM402//"

	img_dirs = [vsem_dir+i for i in os.listdir(vsem_dir)]
	dir_time_stamp = lambda x: datetime.datetime.fromtimestamp(os.stat(x).st_mtime)
	dir_age_sec = lambda x: (datetime.datetime.today() - dir_time_stamp(x)).total_seconds()
	recent_dirs = list(filter((lambda x: dir_age_sec(x) < seconds_lookback), img_dirs)) #img dirs less than a seconds_lookback old
	meas_dirs = [[i+"//"+obs_folder_name+"//", os.path.split(i)[1]] for i in recent_dirs if obs_folder_name in os.listdir(i)] #img dirs and	 MeasDisplay path.
	'''
	meas_dirs: list of list, each index in list has two indices
	1) full file path to MeasDisplay directory for a  lot that is less than seconds_lookback old. :
	"home//ccag//Desktop//Vera402//images//AutoSave//Production//Production//VSEM402//lotnum_recipe//MeasDisplay//"
	2) base folder name in image directory on tool:
		"lotnum_recipe_PortNumber_SlotNumber,1"
		-The above is used to get port number to be populated in db.
	'''
	return meas_dirs

#full file path of metadata file plus img directory "lotnum_recipe_PortNumber_SlotNumber"
def meta_data(file_path, img_dir):
	dir_time_stamp = lambda x: datetime.datetime.fromtimestamp(os.stat(x).st_mtime)
	img_file_path = os.path.split(file_path)[0] + "//"+ os.path.split(file_path)[1][1:]
	img_dir_date = dir_time_stamp(os.path.split(os.path.split(file_path)[0])[0])
	if os.path.isfile(img_file_path):
		port = int(img_dir.split("_")[-2][1])

		dir_time_stamp = lambda x: datetime.datetime.fromtimestamp(os.stat(x).st_mtime)
		with open(file_path,'r') as f:
			file_lines = [tic.strip() for tic in f.readlines() if tic.strip()]
		#Pull data by index of line.
		#Will need to be changed if meta data file format changes.
		#Possible entry name changes in the file itself prevents
		#filtering/sorting data by name.

			#		  '''
			# 0		   FOV: 1.22 m
			# 1		   BE: 500 V
			# 2		   Vhar: 0 V
			# 3		   Tilt: N, 0.0
			# 4		   Ip: Low
			# 5		   B.TV: 1/2 sec
			# 6		   Lot: VRTY_CCAG_T2
			# 7		   Rcp: CCAG_PITCH_TEST_VRTY
			# 8		   CH500_HOR_CCD: CH500_HOR_CCD
			# 9		   Slot: 12
			# 10		Site: MEAS 12
			# 11		Field: 0_-3
			# 12		Abs. Loc.:
			# 13		-378.53
			# 14		-24505.39
			# 15		ToolId: Verity401
			# 16		Wed 08:56:45
			# 17		Jan 29	2020
			# 18		Description:
			#		  '''

		if len(file_lines) > 17:
			assert file_lines[0].split(":")[0].strip() == "FOV"
			assert file_lines[6].split(":")[0].strip() == "Lot"
			assert file_lines[9].split(":")[0].strip() == "Slot"
			assert file_lines[10].split(":")[0].strip() == "Site"
			assert file_lines[11].split(":")[0].strip() == "Field"


			try:
				output_data = [
								int(file_lines[9].split(":")[1]),
								float(file_lines[0].split(":")[1].split()[0]),
								file_lines[4].split(":")[1].strip(),
								file_lines[6].split(":")[1].strip(),
								int(file_lines[1].split(":")[1].split()[0]),
								int(file_lines[2].split(":")[1].split()[0]),
								file_lines[7].split(":")[1].strip(),
								file_lines[10].split(":")[1].split()[0].strip(),
								int(file_lines[10].split(":")[1].split()[1]),
								int(file_lines[11].split(":")[1].split("_")[0]),
								int(file_lines[11].split(":")[1].split("_")[1]),
								float(file_lines[13]),
								float(file_lines[14]),
								dir_time_stamp(file_path),
								port,
								int(file_path[-1]),
								file_lines[8].split(":")[0].strip(),
								img_dir_date,
								img_file_path]
			except:
				output_data = None
		else:
			output_data = None

	return output_data
def sem_image_info_scrape_and_prep(meas_dirs):
	dir_time_stamp = lambda x: datetime.datetime.fromtimestamp(os.stat(x).st_mtime)
	dir_age_sec = lambda x: (datetime.datetime.today() - dir_time_stamp(x)).total_seconds()
	info = []
	for meas_dir, img_dir in meas_dirs:
		lot_info = []
		#get metafile paths of each image stored in the MeasDisplay folder
		meta_files = [meas_dir + i for i in os.listdir(meas_dir) if "."==i[0]] #full metafile path.
		if meta_files:
			#get file age for each metafile, if the newest one is less than 10 minutes old the
			#lot may still be measuring. Don't pull that data yet.
			file_seconds = [dir_age_sec(f) for f in meta_files]
			if min(file_seconds) > 600:
				for meta_file in meta_files:
					#metafile: full file path to meta
					img_file_info = meta_data(meta_file, img_dir)
					# for slot,fov,iprobe,lot,vacc,vhar,recipe,site_type,site_order,fieldx,fieldy,locx,locy,date,port,cycle,target,measdate,image in img_file_info:
					#	  assert type(slot) == int
					#	  assert type(fov) == float
					#	  assert type(iprobe) == str
					#	  assert type(lot) == str
					#	  assert type(vacc) == int
					#	  assert type(vhar) == int
					#	  assert type(recipe) == str
					#	  assert type(site_type) == str
					#	  assert type(site_order) == int
					#	  assert type(fieldx) == int
					#	  assert type(fieldy) == int
					#	  assert type(locx) == float
					#	  assert type(locy) == float
					#	  assert type(date) == datetime.datetime
					#	  assert type(port) == int
					#	  assert type(cycle) == int
					#	  assert type(target) == str
					#	  assert type(measdate) == datetime.datetime
					#	  assert type(image) == str
					if img_file_info:
						lot_info.append(img_file_info)
		info.append(lot_info)
	return info

def test1():
	dir_time_stamp = lambda x: datetime.datetime.fromtimestamp(os.stat(x).st_mtime)
	dir_age_sec = lambda x: (datetime.datetime.today() - dir_time_stamp(x)).total_seconds()
	vsem_dir = "//home//ccag//Desktop//vera401//images//AutoSave//Production//Production//VSEM401//"
	seconds_lookback = 60*60*2
	obs_folder_name = "PatternFov"
	meas_dirs = sem_img_gather_folders(vsem_dir, seconds_lookback, obs_folder_name)

	print("Check first entry return from sem_img_gather_folders, meas_dirs[0][0]")
	print("first dir pulled: ", meas_dirs[0][0])
	print("dir date of creation " , dir_time_stamp(meas_dirs[0][0]))

	info = sem_image_info_scrape_and_prep(meas_dirs)

	print('First lot image info pulled')
	for i in info[0]:
		print(i)

	tic = info[0]
	for slot,fov,iprobe,lot,vacc,vhar,recipe,site_type,site_order,fieldx,fieldy,locx,locy,date,port,cycle,target,measdate,image in tic:
		assert type(slot) == int
		assert type(fov) == float
		assert type(iprobe) == str
		assert type(lot) == str
		assert type(vacc) == int
		assert type(vhar) == int
		assert type(recipe) == str
		assert type(site_type) == str
		assert type(site_order) == int
		assert type(fieldx) == int
		assert type(fieldy) == int
		assert type(locx) == float
		assert type(locy) == float
		assert type(date) == datetime.datetime
		assert type(port) == int
		assert type(cycle) == int
		assert type(target) == str
		assert type(measdate) == datetime.datetime
		assert type(image) == str
	print('done')

def db_init(db_file, db_table):
	try:
		conn = sqlite3.connect(db_file, detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
		cur = conn.cursor()
		sql_input = '''CREATE TABLE if not exists %s(
						id INTEGER PRIMARY KEY,
						tool TEXT NOT NULL,
						slot INTEGER NOT NULL,
						fov REAL NOT NULL,
						iprobe TEXT NOT NULL,
						lot TEXT NOT NULL,
						vacc INTEGER NOT NULL,
						vhar INTEGER NOT NULL,
						recipe TEXT NOT NULL,
						site_type TEXT NOT NULL,
						site_order INTEGER NOT NULL,
						fieldx INTEGER NOT NULL,
						fieldy INTEGER NOT NULL,
						locx REAL NOT NULL,
						locy REAL NOT NULL,
						date timestamp NOT NULL,
						port INTEGER NOT NULL,
						cycle INTEGER NOT NULL,
						target TEXT NOT NULL,
						measdate timestamp NOT NULL,
						image BLOB NOT NULL,
						unique(
						tool,
						slot,
						fov,
						iprobe,
						lot,
						vacc,
						vhar,
						recipe,
						site_type,
						site_order,
						fieldx,
						fieldy,
						locx,
						locy,
						date,
						port,
						cycle,
						target,
						measdate));''' % db_table
		cur.execute(sql_input)
		conn.commit()
		cur.close()
		print("DB %s, Table %s created sucessfully \n" %(db_file, db_table))
	except sqlite3.Error as error:
		print("Error while working with SQlite: ", error)
	finally:
		if (conn):
			conn.close()
def sem_image_laber(data):
	lineThickness = 2
	slot_num = str(data[0])
	lot_num = data[3]
	img_fov = data[1]
	legend_number = int(img_fov/3)
	if legend_number ==0:
		legend_number = np.round(img_fov/3,1)
	obs_col = str(data[9])
	obs_row = str(data[10])
	img_og = cv2.imread(data[-1])
	cv2.putText(img = img_og, text=str(legend_number)+" um", org=(10,450),fontFace=1, fontScale=2, color=(0,255,0), thickness=2)
	#Scale Bar Line, bottom left
	cv2.line(img_og, (10, 460), (int(480*(legend_number/img_fov))+10, 460), (0,255,0), lineThickness)
	#FOV label, top right
	cv2.putText(img=img_og, text="FOV: "+str(img_fov)+" um", org=(350,20),fontFace=1, fontScale=1, color=(0,255,0), thickness=2)
	#Lot number, top left
	cv2.putText(img=img_og, text="Lot: "+str(lot_num), org=(50,20),fontFace=1, fontScale=1, color=(0,255,0), thickness=2)
	#Wafer number, top left
	cv2.putText(img=img_og, text="Slot: "+str(slot_num), org=(50,50),fontFace=1, fontScale=1, color=(0,255,0), thickness=2)
	#Field, bottom right
	cv2.putText(img=img_og, text="Field: "+str(obs_col) + " , " + str(obs_row), org=(350,460),fontFace=1, fontScale=1, color=(0,255,0), thickness=2)
	_, encoded_image = cv2.imencode('.jpg', img_og)
	img_binary = sqlite3.Binary(encoded_image.tobytes())
	return img_binary
def sem_image_to_binary(img_file_path):
	img_og = cv2.imread(img_file_path)
	_, encoded_image = cv2.imencode('.jpg', img_og)
	img_binary = sqlite3.Binary(encoded_image.tobytes())
	return img_binary
def insert_data(db_file, db_table, input_data, obs_img_bool):
	data = input_data[:]
	try:
		conn = sqlite3.connect(db_file, detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
		cur = conn.cursor()
		sql_insert = '''INSERT INTO '%s'
						('tool',
						'slot',
						'fov',
						'iprobe',
						'lot',
						'vacc',
						'vhar',
						'recipe',
						'site_type',
						'site_order',
						'fieldx',
						'fieldy',
						'locx',
						'locy',
						'date',
						'port',
						'cycle',
						'target',
						'measdate',
						'image'
						)
						VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'''%db_table
		if obs_img_bool:
			data[-1] = sem_image_laber(data)
		else:
			data[-1] = sem_image_to_binary(data[-1])
		cur.execute(sql_insert, data)
		conn.commit()
		cur.close()
		return_data = data[:]
		print('data added')
	except sqlite3.Error as error:
		print("SQLite error: ", error)
		return_data = None
	finally:
		if (conn):
			conn.close()
	return return_data

def insert_data_dev(table, new_data, db_file_flask):
	try:
		conn = sqlite3.connect(db_file_flask, detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
		cur = conn.cursor()
		sql_insert = '''INSERT INTO '%s'
						('tool',
						'slot',
						'fov',
						'iprobe',
						'lot',
						'vacc',
						'vhar',
						'recipe',
						'site_type',
						'site_order',
						'fieldx',
						'fieldy',
						'locx',
						'locy',
						'date',
						'port',
						'cycle',
						'target',
						'measdate',
						'image')
						VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'''%table
		cur.execute(sql_insert, new_data)
		conn.commit()
		cur.close()
		conn.close()
		print('data add flask')
	except sqlite3.Error as error:
		print("Error while working with SQLite flask side: ", error)
	finally:
		if conn:
			conn.close()

def start_scrape_and_db_pop(seconds_lookback, db_file, db_table, vsem_dir, obs_folder_name, new_table, tool, obs_img_bool,add_to_flask_db,db_file_flask):
	#Create backup db if it doesn't already exist
	db_init(db_file, db_table)
	#meas_dirs: n by 2 list of lists. each list is 2 indices long. [full_file_path to "MeasDisplay" folder, "lotnum_recipe_PortNumber_SlotNumber,1"]
	meas_dirs = sem_img_gather_folders(vsem_dir, seconds_lookback, obs_folder_name)

	lot_info = sem_image_info_scrape_and_prep(meas_dirs)
	return_lots = []
	for lot in lot_info:
		return_lot_info = []
		for tic in lot:
			if obs_img_bool:
				real_obs_target = ["OBS","SAM"]
				if all(x in os.path.splitext(os.path.split(tic[-1])[1])[0] for x in real_obs_target):
					tic.insert(0,tool)
					return_tic = insert_data(db_file, db_table, tic, obs_img_bool)
					if return_tic:
						return_lot_info.append(return_tic)
			else:
				tic.insert(0,tool)
				return_tic = insert_data(db_file, db_table, tic, obs_img_bool)
				if return_tic:
					return_lot_info.append(return_tic)
		return_lots.append(return_lot_info)
	if add_to_flask_db:
		for lot in return_lots:
			for tic in lot:
				insert_data_dev(new_table, tic, db_file_flask)



if __name__ =="__main__":
	expected_number_of_argvs = 1 + 2 #first argv is always script name....
	argv_error_statement = '''
	Argv variables looking for: 
	[1] number of days to lookback and pull data from, type integer.
	[2] add the image data to the main flask database, True or False, type str.
	'''
	
	if not len(sys.argv) == expected_number_of_argvs:
		print("Lacking correct number of arg variables!")
		print(argv_error_statement)
		print("Exiting Script, no data pulled")
		sys.exit(1)
	
	#db_file = "/home/ccag/Python_Scripts/sem_img_db/backup_db.sqlite"
	#db_file_flask = "/home/ccag/Python_Scripts/sem_flask_alchemy/data-dev.sqlite"

	#backup db
	db_file = os.getenv('backup_db_path')
	
	#main flask db
	db_file_flask = os.getenv('main_db_path')
	number_days_look_back = int(sys.argv[1])
	number_minutes_lookback =  60 * 24 * number_days_look_back
	seconds_lookback = 60*number_minutes_lookback
	add_to_flask_db = sys.argv[2].lower() == 'true'
	
	
	if (not os.path.isfile(db_file_flask)) and add_to_flask_db:
		print("\nMain flask db is not available!")
		print("\nScript is trying to add data to flask db!")
		print("\nExiting script! No Scrape for you")
		sys.exit(1)
	
	#path = "//netapp4.cmi.cypress.com//usr4//DOSexe//ufiles//F4PHOTO//SEM_IMG_DUMP//"
	sem_img_dump_path = os.getenv("sem_img_dump_path")
	this_month_directory = datetime.datetime.now().strftime("_%B_%Y")
	vera401_dir = sem_img_dump_path + "vera401//" + this_month_directory + "//"
	vera402_dir = sem_img_dump_path + "vera402//"+ this_month_directory + "//"
	verity_dir = sem_img_dump_path + "verity401//"+ this_month_directory + "//"

	#=================================================================
	#======================= MEASDISPLAY / OBS=======================
	#=================================================================
	db_table = "measdisplay_obs"
	obs_folder_name = "MeasDisplay"
	new_table = "measdisplay_obs"

	#=======================VERA401 MEASDISPLAY / OBS=======================
	tool = 'vera401'
	obs_img_bool = True
	print("Starting MeasDisplay Vera401")
	start_scrape_and_db_pop(seconds_lookback, db_file, db_table, vera401_dir, obs_folder_name, new_table, tool, obs_img_bool,add_to_flask_db, db_file_flask)

	#=======================VERA402 MEASDISPLAY / OBS=======================
	tool = 'vera402'
	obs_img_bool = True
	print("Starting MeasDisplay Vera402")
	start_scrape_and_db_pop(seconds_lookback, db_file, db_table, vera402_dir, obs_folder_name, new_table, tool, obs_img_bool,add_to_flask_db,db_file_flask)

	#=======================VERITY401 MEASDISPLAY / OBS=======================
	tool = 'verity401'
	obs_img_bool = True
	print("Starting MeasDisplay Verity401")
	start_scrape_and_db_pop(seconds_lookback, db_file, db_table, verity_dir, obs_folder_name, new_table, tool, obs_img_bool,add_to_flask_db,db_file_flask)

	#==========================================================
	#======================= PATTERNFOV =======================
	#==========================================================
	db_table = "patternfov"
	obs_folder_name = "PatternFov"
	new_table = "patternfov"
	#=======================VERA401 PATTERNFOV =======================
	tool = 'vera401'
	obs_img_bool = False
	print("Starting PatternFOV Vera401")
	start_scrape_and_db_pop(seconds_lookback, db_file, db_table, vera401_dir, obs_folder_name, new_table, tool, obs_img_bool,add_to_flask_db,db_file_flask)

	#=======================VERA402 PATTERNFOV =======================
	tool = 'vera402'
	obs_img_bool = False
	print("Starting PatternFOV Vera402")
	start_scrape_and_db_pop(seconds_lookback, db_file, db_table, vera402_dir, obs_folder_name, new_table, tool, obs_img_bool,add_to_flask_db,db_file_flask)

	#=======================VERITY401 PATTERNFOV =======================
	tool = 'verity401'
	obs_img_bool = False
	print("Starting PatternFOV Verity401")
	start_scrape_and_db_pop(seconds_lookback, db_file, db_table, verity_dir, obs_folder_name, new_table, tool, obs_img_bool,add_to_flask_db,db_file_flask)









	#
