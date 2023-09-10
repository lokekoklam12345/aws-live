from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.tarc.edu.my')


@app.route("/fetchdata", methods=['POST'])
def GetEmp():
    lec_id = request.form['lec_id']
    select_sql = "SELECT * FROM lecturer WHERE lectId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (lec_id,))
        lecturer = cursor.fetchone()

        if not lecturer:
            return "Lecturer not found"

        lec_id = lecturer[0]
        passowrd = lecturer[1]
        name = lecturer[2]
        gender = lecturer[3]
        email = lecturer[4]
        expertis = lecturer[5]

        # Fetch the S3 image URL based on emp_id
        lec_image_file_name_in_s3 = "lec-id-" + str(lec_id) + "_image_file"
        s3 = boto3.client('s3')
        bucket_name = custombucket

        try:
            response = s3.generate_presigned_url('get_object',
                                                 Params={'Bucket': bucket_name,
                                                         'Key': lec_image_file_name_in_s3},
                                                 ExpiresIn=3600)  # Adjust the expiration time as needed

            # You can return the employee details along with the image URL
            emp_details = {
                "lec_id": lec_id,
                "passowrd": passowrd,
                "name": name,
                "gender": gender,
                "email": email,
                "expertis": expertis,
                "image_url": response
            }

            return render_template('GetLecOutput.html',image_url=response,id=lec_id ,psw=passowrd, name=name , email=email , expertis =expertis,gender=gender )

        except Exception as e:
            return str(e)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/editlec", methods=['POST'])
def UpdateEmp():
    lec_id = request.form['lec_id']
    password = request.form['password']
    name = request.form['name']
    gender = request.form['gender']
    email = request.form['email']
    expertis = request.form['expertis']
    lec_image_file = request.files['lec_image_file']

    update_sql = "UPDATE lecturer SET password=%s, name=%s, gender=%s, email=%s, expertise=%s WHERE lectId=%s"
    cursor = db_conn.cursor()

    if lec_image_file.filename == "":
        return "Please select a file"

    try:
        # Check if the employee exists
        check_sql = "SELECT * FROM lecturer WHERE lectId = %s"
        cursor.execute(check_sql, (lec_id,))
        existing_lecturer = cursor.fetchone()

        if not existing_lecturer:
            return "Lecturer not found"

        cursor.execute(update_sql, (password, name, gender, email, expertis,lec_id))
        db_conn.commit()
        lec_name = "" + name 

        # Update image file in S3
        lec_image_file_name_in_s3 = "lec-id-" + str(lec_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data updated in MySQL RDS... updating image in S3...")
            s3.Bucket(custombucket).put_object(Key=lec_image_file_name_in_s3, Body=lec_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location.get('LocationConstraint'))

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                lec_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modifications done...")
    return render_template('UpdateEmpOutput.html', name=name)

    



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

