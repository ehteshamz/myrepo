from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    Response,
    flash,
)
import os
import boto3
from fileinput import filename
import time

# import cv2
application = Flask(__name__)

# Define the access keys
region = "us-east-1"
accessKeyId = os.environ.get("AccessKeyId")
secretAccessKey = os.environ.get("SecretAccessKey")
bucket = os.environ.get("BucketName")
# cam = cv2.VideoCapture(0)


# S3 client
s3 = boto3.client(
    "s3",
    region_name=region,
    aws_access_key_id=accessKeyId,
    aws_secret_access_key=secretAccessKey,
)

# Rekognition client
rekognition = boto3.client(
    "rekognition",
    region_name=region,
    aws_access_key_id=accessKeyId,
    aws_secret_access_key=secretAccessKey,
)


@application.route("/")
@application.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    # 	global switch,camera
    if (
        request.method == "POST"
        and request.form["username"] != ""
    ):
        username = request.form["username"]
        if (not os.path.isfile("loginImage.png")):
            imagefile = request.files["file"]
            imagefile.save("loginImage.png")
            # Upload the file provided by the user in an S3 bucket
        try:
            s3.upload_file("loginImage.png", bucket, username + "loginimg.png")
            os.remove("loginImage.png")
        except:
            msg = "There was a problem during login"
            return render_template("login.html", msg=msg)
        # 		elif request.form.get('click') == 'Capture':

        try:
            reko_response = rekognition.compare_faces(
                SimilarityThreshold=75,
                SourceImage={"S3Object": {"Bucket": bucket, "Name": username + ".png"}},
                TargetImage={
                    "S3Object": {"Bucket": bucket, "Name": username + "loginimg.png"}
                },
            )

            # Delete the object created during login
            s3.delete_object(Bucket=bucket, Key=username + "loginimg.png")

            if len(reko_response["FaceMatches"]) == 0:
                message = ("Username does not exist",)
                return render_template("login.html", message=message)
            elif reko_response["FaceMatches"][0]["Similarity"] > 85:
                message = "Logged in successfully !"
                return render_template("index.html", message=message)
            else:
                message = "Incorrect image !"
                return render_template("login.html", message=message)
        except:
            message = "Error! Please try again"
            return render_template("login.html", message=message)
    else:
        message = "Please provide your credentials"
        return render_template("login.html", message=message)


@application.route("/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)
    return redirect(url_for("login"))


@application.route("/image", methods=["POST"])
def image():

    imagefile = request.files["image"]  # get the image
    imagefile.save("registerImage.png")


@application.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    # 	global switch,camera
    if (
        request.method == "POST"
        and request.form["username"] != ""
    ):
        username = request.form["username"]
        if (not os.path.isfile("registerImage.png")):
            imagefile = request.files["file"]
            imagefile.save("registerImage.png")
            # Upload the file provided by the user in an S3 bucket
        try:
            s3.upload_file("registerImage.png", bucket, username + ".png")
            msg = "Registered Successfully!"
            os.remove("registerImage.png")
            return render_template("login.html", msg=msg)
        except:
            msg = "There was a problem during registration"
            return render_template("register.html", msg=msg)
        # 		elif request.form.get('click') == 'Capture':

    else:
        msg = "Please fill out the form!"
        return render_template("register.html", msg=msg)
    return render_template("register.html", msg=msg)


@application.route("/index")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000)
