import cv2
import requests
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import json
import numpy as np
from thread import start_new_thread
import imutils
import random
import kairos_face
import qrtools
import dlib
def blend_transparent(face_img, overlay_t_img):
	# Split out the transparency mask from the colour info
	overlay_img = overlay_t_img[:,:,:3] # Grab the BRG planes
	overlay_mask = overlay_t_img[:,:,3:]  # And the alpha plane

	# Again calculate the inverse mask
	background_mask = 255 - overlay_mask

	# Turn the masks into three channel, so we can use them as weights
	overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
	background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)

	# Create a masked out face image, and masked out overlay
	# We convert the images to floating point in range 0.0 - 1.0
	face_part = (face_img * (1 / 255.0)) * (background_mask * (1 / 255.0))
	overlay_part = (overlay_img * (1 / 255.0)) * (overlay_mask * (1 / 255.0))

	# And finally just add them together, and rescale it back to an 8bit integer image    
	return np.uint8(cv2.addWeighted(face_part, 255.0, overlay_part, 255.0, 0.0))
#Prep API and camera
def smiling(image):
	smileCascade = cv2.CascadeClassifier("haarcascade_smile.xml")
	roi_gray = cv2.cvtColor(image,cv2.BGR2GRAY)
	smile = smileCascade.detectMultiScale(roi_gray,scaleFactor= 1.7,minNeighbors=22,minSize=(25, 25),flags=cv2.cv.CV_HAAR_SCALE_IMAGE)
	return len(smile) > 0


img2 = None
emote = []
app_id = 'e55384cd'
app_key = 'f7ba2f6a6e0c2d3ad2ac83b661cbf409'
kairos_face.settings.app_id = 'e55384cd'
kairos_face.settings.app_key = 'f7ba2f6a6e0c2d3ad2ac83b661cbf409'
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 10
rawCapture = PiRGBArray(camera, size=(640, 480))
faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")
rects = []
#capture a clean image and write it to the current folder
count = 1
inThread = False
inThreadDetect = False
inQRThread = False
def detect(img):
	print "inThreadDetect"
	global rects
	global inThreadDetect
	global inThread
	rectls = faceCascade.detectMultiScale(img, 1.3, 4, cv2.cv.CV_HAAR_SCALE_IMAGE, (20,20))
	print rectls
	if len(rectls) == 0:
		inThreadDetect = False
	else:
		rectls[:, 2:] += rectls[:, :2]
		print rectls
		rects = rectls.copy()
		if not inThread:
			inThread = True
			cv2.imwrite('image.png',img)
			start_new_thread(doNetworking,())
		inThreadDetect = False
	print "OutThreadDetect"
def doNetworking():
	global emote
	global inThread
	print "InNetworking"
	r = requests.post("https://api.kairos.com/v2/media",files={'source': open('image.png', 'rb')},headers={'app_id':app_id,'app_key':app_key})
	dct = json.loads(r.text)
	if "frames" in dct and len(dct['frames'])>0 and 'people' in dct['frames'][0] and len(dct['frames'][0]['people'])>0:
		emote=[]
		for person in dct['frames'][0]['people']:
			emotions = person['emotions']
			maxEmot = [list(emotions.keys())[0],emotions[list(emotions.keys())[0]]]
			for key in emotions:
				if emotions[key] > maxEmot[1]:
					maxEmot = [key,emotions[key]]
			print "You're "+maxEmot[0]
			emote.append(cv2.imread(maxEmot[0]+".png",-1))
		print "Check out your new image!"
		start_new_thread(doWinston,(dct,))
	else:
		print "Didn't work :("
	print "leavingNetworking"
	inThread = False
def doWinston(dct):
	global location
	idd = -1
	dct['frames'][0]['people'][0]['location'] = location
	try:
		#Try to find current person in database, if not, enroll them
		ans = kairos_face.recognize_face(file='image.png', gallery_name='test')
		if 'Errors' in ans:
			print ans['Errors'][0]['Message']
		elif len(ans['images'][0]['candidates'])==0:
			print "Nobody found! Time to enroll!"
			idd = hex(random.randint(1,100000000000))
			enr = kairos_face.enroll_face(file='image.png', subject_id=idd, gallery_name='test')
			dct['frames'][0]['people'][0]['id'] = idd
			requests.post("https://za4fvvbnvd.execute-api.us-east-2.amazonaws.com/Hackathon/emotions",json=dct)
		else:
			idd = ans['images'][0]['transaction']['subject_id']
			print idd+" welcome back!"
			dct['frames'][0]['people'][0]['id'] = idd
			requests.post("https://za4fvvbnvd.execute-api.us-east-2.amazonaws.com/Hackathon/emotions",json=dct)
	except:
		#Runs if gallery not found (database dumped)
		print "Nobody found! Time to enroll!"
		try:
			idd = hex(random.randint(1,100000000000))
			enr = kairos_face.enroll_face(file='image.png', subject_id=idd, gallery_name='test')
			dct['frames'][0]['people'][0]['id'] = idd
			requests.post("https://za4fvvbnvd.execute-api.us-east-2.amazonaws.com/Hackathon/emotions",json=dct)
		except Exception, e:
			print e
def doQR():
	global inQRThread
	global name
	qr = qrtools.QR()
	if qr.decode('bar.png'):
		st = qr.data
		if "id=" in st:
			open("name.txt",'w').write(st.replace("id=",""))
		elif "location=" in st:
			requests.post("https://za4fvvbnvd.execute-api.us-east-2.amazonaws.com/Hackathon/locations",json={"name":open("name.txt").read(),"location":st.replace("location=","")})
	inQRThread = False
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	image = frame.array
	image = imutils.rotate(image, 270)
	img2 = image.copy()
	rawCapture.truncate(0)
	if not inQRThread:
		inQRThread = True
		cv2.imwrite('bar.png',img2)
		start_new_thread(doQR,())
	if not inThreadDetect:
		inThreadDetect = True
		start_new_thread(detect,(img2.copy(),))
	if emote!=[] and len(rects) >= len(emote):
		for a in xrange(len(emote)):
			x1 = rects[a][0]
			y1 = rects[a][1]
			x2 = rects[a][2]
			y2 = rects[a][3]
			curEmote = emote[a]
			curEmote = cv2.resize(curEmote,(x2-x1,y2-y1))
			blended = blend_transparent(img2[y1:y1+curEmote.shape[0],x1:x1+curEmote.shape[1]],curEmote)
			img2[y1:y1+blended.shape[0],x1:x1+blended.shape[1]] = blended
