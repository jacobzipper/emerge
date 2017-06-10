import cv2
import kairos_face
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
#Prep API and camera
kairos_face.settings.app_id = 'e55384cd'
kairos_face.settings.app_key = 'f7ba2f6a6e0c2d3ad2ac83b661cbf409'
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))
time.sleep(.1)
#capture a clean image and write it to the current folder
cont = 'y'
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	image = frame.array
	cv2.imwrite('image.png',image)
	rawCapture.truncate(0)
	try:
		#Try to find current person in database, if not, enroll them
		ans = kairos_face.recognize_face(file='image.png', gallery_name='test')
		if 'Errors' in ans:
			print ans['Errors'][0]['Message']
		elif len(ans['images'][0]['candidates'])==0:
			print "Nobody found! Time to enroll!"
			enr = kairos_face.enroll_face(file='image.png', subject_id=raw_input("What is your name: "), gallery_name='test')
		else:
			print "Hello "+ans['images'][0]['transaction']['subject_id']+"!"
	except:
		#Runs if gallery not found (database dumped)
		print "Nobody found! Time to enroll!"
		try:
			enr = kairos_face.enroll_face(file='image.png', subject_id=raw_input("What is your name: "), gallery_name='test')
			print enr
		except:
			print "An error occurred. Please try again."
	#Drop database to redo pictures and recognition
	if raw_input("Dump database? (y/n): ")=='y':
		try:
			kairos_face.remove_gallery('test')
			print "Gallery deleted."
		except:
			print "Gallery does not exist."
	cont = raw_input("Continue? (y/n): ")
	if cont=='n':
		break