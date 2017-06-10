import cv2
import base64
import kairos_face
#Prep API and camera
kairos_face.settings.app_id = 'e55384cd'
kairos_face.settings.app_key = 'f7ba2f6a6e0c2d3ad2ac83b661cbf409'
camera = cv2.VideoCapture(0)
#capture a clean image and write it to the current folder
def doImage():
	for a in xrange(30):
		camera.read()
	retval, img = camera.read()
	cv2.imwrite('image.png',img)
cont = 'y'
while cont!='n':
	doImage()
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