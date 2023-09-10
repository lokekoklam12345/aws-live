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

            return render_template('GetEmpOutput.html',image_url=response,id=emp_id ,f_name=first_name, l_name=last_name , skill=pri_skill , loc=location )

        except Exception as e:
            return str(e)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()


    



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

