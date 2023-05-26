from flask import Flask, render_template, request, redirect, url_for, session, Response,flash
import os
import boto3
from fileinput import filename
import cv2
application = Flask(__name__)

#Define the access keys
region = 'us-east-1'
accessKeyId = os.environ.get('AccessKeyId')
secretAccessKey = os.environ.get('SecretAccessKey')
bucket = os.environ.get('BucketName')
cam = cv2.VideoCapture(0)

def get_stream():
    while True:
        success, frame = cam.read()
        if success:
            _ , buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


#S3 client
s3 = boto3.client("s3", region_name=region,aws_access_key_id=accessKeyId,
         aws_secret_access_key=secretAccessKey)

#Rekognition client
rekognition = boto3.client('rekognition', region_name=region,aws_access_key_id=accessKeyId,
         aws_secret_access_key=secretAccessKey)

@application.route('/')
@application.route('/login', methods =['GET', 'POST'])
def login():
	message = ''
	global switch,camera
	if request.method == 'POST':
		username = request.form['username']
		if request.files['file'].filename != '':
			imagefile = request.files['file']
			imagefile.save(imagefile.filename)
			#Upload the file provided by the user in an S3 bucket
			try:
				s3.upload_file(imagefile.filename, bucket, username + 'loginimg.png')
			except:
				message = 'There was a problem'
		elif request.form.get('click') == 'Capture':
			cam = cv2.VideoCapture(0)
			result, image = cam.read()
			if result:
				cv2.imwrite("userimagelogin.png", image)
				#Upload the file provided by the user in an S3 bucket
				try:
					s3.upload_file("userimagelogin.png", bucket, username + 'loginimg.png')
				except:
					message = 'There was a problem'
		else:
			message = "Please fill out the form"
			return render_template('login.html', message = message)
		
		#Use Amazon Rekognition	to compare the files provided by the user
		try:
			reko_response = rekognition.compare_faces(SimilarityThreshold=75,
                                    SourceImage={'S3Object':{'Bucket':bucket,'Name':username + ".png"}},
									TargetImage={'S3Object':{'Bucket':bucket,'Name':username + "loginimg.png"}})
		
			#Delete the object created during login
			s3.delete_object(Bucket=bucket, Key=username + 'loginimg.png')

			if len(reko_response["FaceMatches"])==0:
				message = 'Username does not exist',
				return render_template('login.html', message = message)
			elif  reko_response['FaceMatches'][0]['Similarity'] > 85:
				message = 'Logged in successfully !'
				return render_template('index.html', message = message)
			else:
				message = 'Incorrect image !'
				return render_template('login.html', message = message)
		except:
			message = "Error! Please try again"
			return render_template('login.html', message = message)
	else: 
		message = "Please provide your credentials"
		return render_template('login.html', message = message)

@application.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	return redirect(url_for('login'))

@application.route('/register', methods =['GET', 'POST'])
def register():
	msg = ''
	global switch,camera
	if (request.method == 'POST' and request.form['username']!='' and (request.files['file'].filename != '' or request.form.get('click') == 'Capture' )) :
		username = request.form['username']
		if request.files['file'].filename != '':
			imagefile = request.files['file']
			imagefile.save(imagefile.filename)
			#Upload the file provided by the user in an S3 bucket
			try:
				s3.upload_file(imagefile.filename, bucket, username + '.png')
				msg = 'Registered Successfully!'
				return render_template('login.html', msg = msg)
			except:
				msg = 'There was a problem during registration'
				return render_template('register.html', msg = msg)
		elif request.form.get('click') == 'Capture':
			cam = cv2.VideoCapture(0)
			result, image = cam.read()
			if result:
				cv2.imwrite("userimage.png", image)
				#Upload the file provided by the user in an S3 bucket
				try:
					s3.upload_file("userimage.png", bucket, username + ".png")
					msg = 'Registered Successfully!'
					return render_template('login.html', msg = msg)
				except:
					msg = 'There was a problem during registration'
					return render_template('register.html', msg = msg)
		else:
			msg = "Please fill out the form"
			return render_template('register.html', msg = msg)
	else:
		msg = 'Please fill out the form!'
		return render_template('register.html', msg = msg)
	return render_template('register.html', msg = msg)

@application.route('/live_stream')
def live_stream():
    return Response(get_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@application.route('/index')
def index():
	return render_template('index.html')


if __name__ == '__main__':
	application.run(host="0.0.0.0",port=5000)
