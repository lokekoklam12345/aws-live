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
    return render_template('GetEmp.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.tarc.edu.my')


@app.route("/fetchdata", methods=['POST'])
def GetEmp():
    emp_id = request.form['emp_id']
    select_sql = "SELECT * FROM employee WHERE emp_id = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (emp_id,))
        employee = cursor.fetchone()

        if not employee:
            return "Employee not found"

        emp_id = employee[0]
        first_name = employee[1]
        last_name = employee[2]
        pri_skill = employee[3]
        location = employee[4]

        # Fetch the S3 image URL based on emp_id
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.client('s3')
        bucket_name = custombucket

        try:
            response = s3.generate_presigned_url('get_object',
                                                 Params={'Bucket': bucket_name,
                                                         'Key': emp_image_file_name_in_s3},
                                                 ExpiresIn=3600)  # Adjust the expiration time as needed

            # You can return the employee details along with the image URL
            emp_details = {
                "emp_id": emp_id,
                "first_name": first_name,
                "last_name": last_name,
                "pri_skill": pri_skill,
                "location": location,
                "image_url": response
            }

            return render_template('GetEmpOutput.html',image_url=response,id=emp_id ,fname=first_name, lname=last_name , interest=pri_skill , location =location )

        except Exception as e:
            return str(e)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/editEmp", methods=['POST'])
def UpdateEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    update_sql = "UPDATE employee SET first_name=%s, last_name=%s, pri_skill=%s, location=%s WHERE emp_id=%s"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        # Check if the employee exists
        check_sql = "SELECT * FROM employee WHERE emp_id = %s"
        cursor.execute(check_sql, (emp_id,))
        existing_employee = cursor.fetchone()

        if not existing_employee:
            return "Employee not found"

        cursor.execute(update_sql, (first_name, last_name, pri_skill, location, emp_id))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name

        # Update image file in S3
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data updated in MySQL RDS... updating image in S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location.get('LocationConstraint'))

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modifications done...")
    return render_template('UpdateEmpOutput.html', name=emp_name)

    



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

