import cv2
import requests
import time
import json
import numpy as np
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
app_id = 'e55384cd'
app_key = 'f7ba2f6a6e0c2d3ad2ac83b661cbf409'
video_capture = cv2.VideoCapture(0)
for a in xrange(30):
	video_capture.read()
#capture a clean image and write it to the current folder
count = 1
br = False
while True:
	ret, image = video_capture.read()
	cv2.imwrite('image.png',image)
	r = requests.post("https://api.kairos.com/v2/media",files={'source': open('image.png', 'rb')},data={'landmarks':1},headers={'app_id':app_id,'app_key':app_key})
	dct = json.loads(r.text)
	if "frames" in dct and len(dct['frames'])>0 and 'people' in dct['frames'][0] and len(dct['frames'][0]['people'])>0:
		img2 = image.copy()
		for person in dct['frames'][0]['people']:
			emotions = person['emotions']
			maxEmot = [list(emotions.keys())[0],emotions[list(emotions.keys())[0]]]
			for key in emotions:
				if emotions[key] > maxEmot[1]:
					maxEmot = [key,emotions[key]]
			print "You're "+maxEmot[0]
			emote = cv2.imread(maxEmot[0]+".png",-1)
			x = person['face']['x']
			y = person['face']['y']
			w = person['face']['width']
			h = person['face']['height']
			emote = cv2.resize(emote, (h, w))
			blended = blend_transparent(img2[y:y+emote.shape[0],x:x+emote.shape[1]],emote)
			img2[y:y+blended.shape[0],x:x+blended.shape[1]] = blended
			cv2.imwrite('image.png',img2)
			br = True
		print "Check out your new image!"
		break
	print "Didn't detect face "+str(count)+" times!"
	count+=1