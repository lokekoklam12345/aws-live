from flask import Flask, render_template, request,session
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
                                                 ExpiresIn=1000)  # Adjust the expiration time as needed

            # You can return the employee details along with the image URL
            lec_details = {
                "lec_id": lec_id,
                "passowrd": passowrd,
                "name": name,
                "gender": gender,
                "email": email,
                "expertis": expertis,
                "image_url": response
            }

            return render_template('GetLecOutput.html',image_url=response,id=lec_id ,psw=passowrd, name=name , email=email , expertise =expertis,gender=gender )

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
    expertise = request.form['expertise']
    lec_image_file = request.files['lec_image_file']

    update_sql = "UPDATE lecturer SET password=%s, name=%s, gender=%s, email=%s, expertise=%s WHERE lectId=%s"
    cursor = db_conn.cursor()     

    try:
        # Check if the employee exists
        check_sql = "SELECT * FROM lecturer WHERE lectId = %s"
        cursor.execute(check_sql, (lec_id,))
        existing_lecturer = cursor.fetchone()

        if not existing_lecturer:
            return "Lecturer not found"

        cursor.execute(update_sql, (password, name, gender, email, expertise,lec_id))
        db_conn.commit()
        lec_name = "" + name 

        if lec_image_file.filename != "":
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

@app.route("/lecHome", methods=['GET','POST'])
def LecHome():
    return render_template('LecturerHome.html')    

@app.route("/leclogin")
def LecLoginPage():
    return render_template('LecturerLogin.html')

@app.route("/loginlec", methods=['GET','POST'])
def LoginLec():

    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        select_sql = "SELECT * FROM lecturer WHERE lectId = %s AND password = %s"
        cursor = db_conn.cursor()


        try:
            cursor.execute(select_sql, (email,password,))
            lecturer = cursor.fetchone()

            if not lecturer:
               # select_sql = "SELECT * FROM student WHERE supervisor = %s"

              #  cursor.execute(select_sql, (lecturer[0],))
              #  students = cursor.fetchall() 
              return render_template('LecturerLogin.html', msg="Access Denied : Invalid email or password")
                
            
        except Exception as e:
            return str(e)

        finally:   
            cursor.close()
        
    return render_template('LecturerHome.html', id=lecturer[0],password=lecturer[1], name=lecturer[2], gender=lecturer[3], email=lecturer[4], expertise=lecturer[5])



@app.route("/displayStudent" ,methods=['GET','POST'])
def GetStudent():
    
    action=request.form['action']
    id=request.form['lec_id']

    if action == 'drop':
        select_sql = f"SELECT * FROM student WHERE supervisor LIKE '%{id}%'"
        cursor = db_conn.cursor()

    if action =='pickUp':
        select_sql = f"SELECT * FROM student WHERE supervisor IS NULL"
        cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql)
        students = cursor.fetchall()  # Fetch all students
               
        student_list = []

        for student in students:
            student_id = student[0]
            name = student[1]
            gender = student[4]
            email = student[6]
            level = student[7]
            programme = student[8]
            cohort = student[10]

            # Fetch the S3 image URL based on student_id
            stu_image_file_name_in_s3 = "stu-id-" + str(student_id) + "_image_file"
            s3 = boto3.client('s3')
            bucket_name = custombucket

            try:
                response = s3.generate_presigned_url('get_object',
                                                     Params={'Bucket': bucket_name,
                                                             'Key': stu_image_file_name_in_s3},
                                                     ExpiresIn=1000)  # Adjust the expiration time as needed

                # Create a dictionary for each student with their details and image URL
                student_data = {
                    "student_id": student_id,
                    "name": name,
                    "gender": gender,
                    "email": email,
                    "level": level,
                    "programme": programme,
                    "cohort": cohort,
                }

                # Append the student's dictionary to the student_list
                student_list.append(student_data)
                

            except Exception as e:
                return str(e)       
         
        if action == 'drop':
         return render_template('DropStudent.html', student_list=student_list,id=id,programme_list=filterProgramme(),cohort_list=filterCohort(),level_list=filterLevel())

        if action =='pickUp': 
         return render_template('PickUpStudent.html',id=id, student_list=student_list,programme_list=filterProgramme(),cohort_list=filterCohort(),level_list=filterLevel())

    except Exception as e:
        return str(e)

    finally:
        cursor.close()


@app.route("/pickUp" ,methods=['GET','POST'])
def PickStudent():
    selected_student_ids = request.form.getlist('selected_students[]')
    #selected_student_name = request.form.getlist('selected_studentsNames[]')
    lec_id = request.form['lec_id']
    #student_id = request.form['student_id']
    #name = request.form['name']
    #gender = request.form['gender']
    #email = request.form['email']
    #level = request.form['level']
    #programme = request.form['programme']
    #cohort = request.files['cohort']
    

    update_sql = "UPDATE student SET supervisor=%s WHERE studentId=%s"
    cursor = db_conn.cursor()    

    try:
        # Check if the employee exists
        for student_id in selected_student_ids:
            update_sql = "UPDATE student SET supervisor=%s WHERE studentId=%s"
            cursor = db_conn.cursor()    
            cursor.execute(update_sql, (lec_id,student_id))
            db_conn.commit()                    

    finally:
        cursor.close()
    
    return render_template('PickedUpOutput.html', student_list=selected_student_ids)

@app.route("/drop" ,methods=['GET','POST'])
def DropStudent():
    selected_student_ids = request.form.getlist('selected_students[]')
    selected_student_name = request.form.getlist('selected_students[]')
    #student_id = request.form['student_id']
    #name = request.form['name']
    #gender = request.form['gender']
    #email = request.form['email']
    #level = request.form['level']
    #programme = request.form['programme']
    #cohort = request.files['cohort']
    
    update_sql = "UPDATE student SET supervisor='' WHERE studentId=%s"
    cursor = db_conn.cursor()    
    try:       
        for student_id in selected_student_ids:
            update_sql = "UPDATE student SET supervisor = NULL WHERE studentId=%s"
            cursor = db_conn.cursor()    
            cursor.execute(update_sql, (student_id))
            db_conn.commit()                    

    finally:
        cursor.close()
    
    return render_template('DropOutput.html', student_list=selected_student_name)

@app.route("/filterStudent" ,methods=['GET','POST'])
def FilterStudent():
    
    level= request.form['search-level']
    programme=request.form['search-programme']
    cohort=request.form['search-cohort']

    select_sql = "SELECT * FROM student WHERE supervisor IS NULL"
    cursor = db_conn.cursor()

    if level != 'All':
          select_sql += f" AND level LIKE '%{level}%'"
    if programme !='All':
          select_sql += f" AND programme LIKE '%{programme}%'"
    if cohort !='All':
          select_sql += f" AND cohort LIKE '%{cohort}%'"

    try:
        cursor.execute(select_sql)
        students = cursor.fetchall()  # Fetch all students



        stu = []
        student_list = []

        for student in students:
            student_id = student[0]
            name = student[1]
            gender = student[4]
            email = student[6]
            level = student[7]
            programme = student[8]
            cohort = student[10]

            # Fetch the S3 image URL based on student_id
            stu_image_file_name_in_s3 = "stu-id-" + str(student_id) + "_image_file"
            s3 = boto3.client('s3')
            bucket_name = custombucket

            try:
                response = s3.generate_presigned_url('get_object',
                                                     Params={'Bucket': bucket_name,
                                                             'Key': stu_image_file_name_in_s3},
                                                     ExpiresIn=1000)  # Adjust the expiration time as needed

                # Create a dictionary for each student with their details and image URL
                student_data = {
                    "student_id": student_id,
                    "name": name,
                    "gender": gender,
                    "email": email,
                    "level": level,
                    "programme": programme,
                    "cohort": cohort,
                }

                # Append the student's dictionary to the student_list
                student_list.append(student_data)
                

            except Exception as e:
                return str(e)       
         
        return render_template('PickUpStudent.html',id=id, student_list=student_list,programme_list=filterProgramme(),cohort_list=filterCohort(),level_list=filterLevel())

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/filterPickedStudent" ,methods=['GET','POST'])
def FilterPickedStudent():
    

    level= request.form['search-level']
    programme=request.form['search-programme']
    cohort=request.form['search-cohort']
    id=request.form['lec_id']

    select_sql = f"SELECT * FROM student WHERE supervisor = '{id}'"
    cursor = db_conn.cursor()

    if level != 'All':
          select_sql += f" AND level LIKE '%{level}%'"
    if programme !='All':
          select_sql += f" AND programme LIKE '%{programme}%'"
    if cohort !='All':
          select_sql += f" AND cohort LIKE '%{cohort}%'"

    try:
        cursor.execute(select_sql)
        students = cursor.fetchall()  # Fetch all students


        stu = []
        student_list = []

        for student in students:
            student_id = student[0]
            name = student[1]
            gender = student[4]
            email = student[6]
            level = student[7]
            programme = student[8]
            cohort = student[10]

            # Fetch the S3 image URL based on student_id
            stu_image_file_name_in_s3 = "stu-id-" + str(student_id) + "_image_file"
            s3 = boto3.client('s3')
            bucket_name = custombucket

            try:
                response = s3.generate_presigned_url('get_object',
                                                     Params={'Bucket': bucket_name,
                                                             'Key': stu_image_file_name_in_s3},
                                                     ExpiresIn=1000)  # Adjust the expiration time as needed

                # Create a dictionary for each student with their details and image URL
                student_data = {
                    "student_id": student_id,
                    "name": name,
                    "gender": gender,
                    "email": email,
                    "level": level,
                    "programme": programme,
                    "cohort": cohort,
                }

                # Append the student's dictionary to the student_list
                student_list.append(student_data)
                

            except Exception as e:
                return str(e)       
         
        return render_template('DropStudent.html', id=id,student_list=student_list,programme_list=filterProgramme(),cohort_list=filterCohort(),level_list=filterLevel())

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route('/login_admin')
def login_admin():
    return render_template('LoginAdmin.html')

@app.route("/loginAdmin", methods=['GET','POST'])
def loginAdmin():
    if request.method == 'POST':
        admin_id = request.form['admin_ID']
        password = request.form['password']

        if admin_id != "a" or password != "1":
            return render_template('LoginAdmin.html')
        #session['logedInAdmin'] = str(admin_id)

    return displayRequest()

@app.route("/displayRequest", methods=['GET','POST'])
def displayRequest():
    select_sql = "SELECT * FROM request WHERE status ='pending'"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql)
        requests = cursor.fetchall()  # Fetch all request
               
        request_list = []

        for requestEdit in requests:
            req_id = requestEdit[0]
            req_attribute = requestEdit[1]
            req_change = requestEdit[2]
            req_reason = requestEdit[4]
            req_studentId = requestEdit[5]

            try:                
                request_data = {
                    "id": req_id,
                    "attribute": req_attribute,
                    "change": req_change,
                    "reason": req_reason,
                    "studentId": req_studentId,
                }

                # Append the student's dictionary to the student_list
                request_list.append(request_data)
                

            except Exception as e:
                return str(e)               

       
    except Exception as e:
        return str(e)

    finally:
        cursor.close()
    
    return render_template('AdminDashboard.html', request_list=request_list,programme_list=filterProgramme(),cohort_list=filterCohort(),level_list=filterLevel())

@app.route("/approveReq", methods=['GET','POST'])
def approveReq():
    selected_request_ids = request.form.getlist('selected_requests[]')
    
    resultAttributes = []  # Store the result attributes here
    resultChange = []
    resultStudentId=[]
    resultOri=[]

    try:
        cursor = db_conn.cursor()
        
        for request_id in selected_request_ids:
            get_attribute = "SELECT attribute FROM request WHERE requestId=%s"
            cursor.execute(get_attribute, (request_id,))
            attribute_result = cursor.fetchone()  # Fetch the result for this request_id

            get_change = "SELECT newData FROM request WHERE requestId=%s"
            cursor.execute(get_change, (request_id,))
            change_result = cursor.fetchone()  # Fetch the result for this request_id

            get_studentId = "SELECT studentId FROM request WHERE requestId=%s"
            cursor.execute(get_studentId, (request_id,))
            studentId_result = cursor.fetchone()  # Fetch the result for this request_id
            
            if attribute_result:
                resultAttributes.append(attribute_result[0])  # Append the attribute value to the list

            if change_result:
                resultChange.append(change_result[0])  # Append the change value to the list

            if studentId_result:
                resultStudentId.append(studentId_result[0])  # Append the change value to the list

            #get ori data
            get_ori = f"SELECT `{attribute_result[0]}` FROM student WHERE studentId=%s"
            cursor.execute(get_ori, (studentId_result,))
            ori_result = cursor.fetchone()  # Fetch the result for this request_id
            
            if ori_result:
                resultOri.append(ori_result[0])  # Append the change value to the list

            # Use string formatting to create the SQL query
            update_sql = f"UPDATE student SET `{attribute_result[0]}` = %s WHERE studentId=%s"
            cursor.execute(update_sql, (change_result[0], studentId_result[0]))
            db_conn.commit()
                
        db_conn.commit()
        
    finally:
        cursor.close()

    #update the status of the request        
    try:       
        for request_id in selected_request_ids:
            update_sql = "UPDATE request SET status = 'approved' WHERE requestId=%s"
            cursor = db_conn.cursor()    
            cursor.execute(update_sql, (request_id,))
            db_conn.commit()                    

    finally:
        cursor.close()
        
    return render_template('requestOutput.html', resultAttributes=resultAttributes,resultChange=resultChange,studentId_result=studentId_result,resultOri=resultOri)


@app.route("/filterRequest" ,methods=['GET','POST'])
def FilterRequest():

    level= request.form['search-level']
    programme=request.form['search-programme']  # Check if the field exists
    cohort=request.form['search-cohort']
    attribute=request.form['search-attribute']

    select_sql = "SELECT * FROM request r ,student s WHERE status ='pending' AND r.studentId = s.studentId "
    cursor = db_conn.cursor()

    if level != 'All':
          select_sql += f" AND s.level LIKE '%{level}%'"
    if programme !='All':
          select_sql += f" AND s.programme LIKE '%{programme}%'"
    if cohort !='All':
          select_sql += f" AND s.cohort LIKE '%{cohort}%'"
    if attribute !='All':
          select_sql += f" AND r.attribute LIKE '%{attribute}%'"

    select_sql += " Order by r.requestId,r.studentId"

    try:
        cursor.execute(select_sql)
        requests = cursor.fetchall()  # Fetch all request
               
        request_list = []

        for requestEdit in requests:
            req_id = requestEdit[0]
            req_attribute = requestEdit[1]
            req_change = requestEdit[2]
            req_reason = requestEdit[4]
            req_studentId = requestEdit[5]

            try:                
                request_data = {
                    "id": req_id,
                    "attribute": req_attribute,
                    "change": req_change,
                    "reason": req_reason,
                    "studentId": req_studentId,
                }

                # Append the student's dictionary to the student_list
                request_list.append(request_data)
                

            except Exception as e:
                return str(e)               

       
    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    


    return render_template('AdminDashboard.html', request_list=request_list,programme_list=filterProgramme(),cohort_list=filterCohort(),level_list=filterLevel())


def filterProgramme():
    selectProgram_sql = "SELECT DISTINCT programme FROM student;"
    cursorProgramme = db_conn.cursor()
    try:
        cursorProgramme.execute(selectProgram_sql)
        programmes = cursorProgramme.fetchall()  # Fetch all request
                
        programme_list = []

        for programmeExits in programmes:
            programme = programmeExits[0]          

            try:                
                programme_data = {
                    "programme": programme,
                }

                # Append the student's dictionary to the student_list
                programme_list.append(programme_data)
            

            except Exception as e:
                return str(e)               

    
    except Exception as e:
        return str(e)

    finally:
        cursorProgramme.close()

    selectCohort_sql = "SELECT * FROM cohort;"
    cursorCohort = db_conn.cursor()
    try:
        cursorCohort.execute(selectCohort_sql)
        cohorts = cursorCohort.fetchall()  # Fetch all request
                
        cohort_list = []

        for cohortExits in cohorts:
            cohort = cohortExits[0]          

            try:                
                cohort_data = {
                    "cohort": cohort,
                }

                # Append the student's dictionary to the student_list
                cohort_list.append(cohort_data)
            

            except Exception as e:
                return str(e)               

    
    except Exception as e:
        return str(e)

    finally:
        cursorCohort.close()

    return programme_list

def filterCohort():
    selectCohort_sql = "SELECT * FROM cohort;"
    cursorCohort = db_conn.cursor()
    try:
        cursorCohort.execute(selectCohort_sql)
        cohorts = cursorCohort.fetchall()  # Fetch all request
                
        cohort_list = []

        for cohortExits in cohorts:
            cohort = cohortExits[0]          

            try:                
                cohort_data = {
                    "cohort": cohort,
                }

                # Append the student's dictionary to the student_list
                cohort_list.append(cohort_data)
            

            except Exception as e:
                return str(e)               

    
    except Exception as e:
        return str(e)

    finally:
        cursorCohort.close()

    return cohort_list

def filterLevel():
    selectLevel_sql = "SELECT DISTINCT level FROM student;"
    cursorLevel = db_conn.cursor()
    try:
        cursorLevel.execute(selectLevel_sql)
        levels = cursorLevel.fetchall()  # Fetch all request
                
        level_list = []

        for levelExits in levels:
            level = levelExits[0]          

            try:                
                level_data = {
                    "level": level,
                }

                # Append the student's dictionary to the student_list
                level_list.append(level_data)
            

            except Exception as e:
                return str(e)               

    
    except Exception as e:
        return str(e)

    finally:
        cursorLevel.close()

    return level_list

@app.route("/displayCompany", methods=['GET','POST'])
def displayCompany():

    select_sql = "SELECT * FROM company WHERE status ='pending'"
    cursor = db_conn.cursor()
    
    try:
        cursor.execute(select_sql)
        companys = cursor.fetchall()  # Fetch all request
               
        company_list = []

        for companyExits in companys:
            company_id = companyExits[0]
            company_password = companyExits[1]
            company_name = companyExits[2]
            company_about = companyExits[3]
            company_address = companyExits[4]
            company_email= companyExits[5]
            company_phone= companyExits[6]            

            try:                
                company_data = {
                    "id": company_id,
                    "password": company_password,
                    "name": company_name,
                    "about": company_about,
                    "address": company_address,
                    "email": company_email,
                    "phone": company_phone,
                    
                }

                # Append the student's dictionary to the student_list
                company_list.append(company_data)
                

            except Exception as e:
                return str(e)               

       
    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    return render_template('displayCompany.html',company_list=company_list)


@app.route("/filterCompany" ,methods=['GET','POST'])
def FilterCompany():

    name= request.form['search-name']
    address=request.form['search-address']  # Check if the field exists   

    select_sql = "SELECT * FROM company WHERE status ='pending'"
    cursor = db_conn.cursor()

    if name :
          select_sql += f" AND name LIKE '%{name}%'"
    if address:
          select_sql += f" AND address LIKE '%{address}%'"
   
   

    try:
            cursor.execute(select_sql)
            companys = cursor.fetchall()  # Fetch all request
                
            company_list = []

            for companyExits in companys:
                company_id = companyExits[0]
                company_password = companyExits[1]
                company_name = companyExits[2]
                company_about = companyExits[3]
                company_address = companyExits[4]
                company_email= companyExits[5]
                company_phone= companyExits[6]            

                try:                
                    company_data = {
                        "id": company_id,
                        "password": company_password,
                        "name": company_name,
                        "about": company_about,
                        "address": company_address,
                        "email": company_email,
                        "phone": company_phone,
                        
                    }

                    # Append the student's dictionary to the student_list
                    company_list.append(company_data)
                    

                except Exception as e:
                    return str(e)               

        
    except Exception as e:
        return str(e)

    finally:
        cursor.close()



    return render_template('displayCompany.html',company_list=company_list)

@app.route("/approveCompany", methods=['GET','POST'])
def approveCompany():
    selected_selected_companys = request.form.getlist('selected_companys[]')
    selected_company_name = request.form.getlist('selected_name[]')
    action = request.form['button-filter']

    
    cursorApprove = db_conn.cursor()
    cursorName = db_conn.cursor()
    cursorReject = db_conn.cursor()   
    name_list = [] 

    if action == 'approve':
        try:
            
            
            for conpanyId in selected_selected_companys:
                update_sql = "UPDATE company SET status ='activeted' WHERE companyId=%s"
                cursorApprove.execute(update_sql, (conpanyId))
                db_conn.commit()

                selectName_sql = "SELECT name FROM company WHERE companyId=%s;"                
                cursorName.execute(selectName_sql, (conpanyId))
                names = cursorName.fetchall()  # Fetch all request

                for nameExits in names:
                    name = nameExits[0]

            
                try:
                    name_data = {
                        "name": name,
                    }
                    name_list.append(name_data)
                except Exception as e:
                    return str(e)
        finally:
            cursorApprove.close()
            cursorName.close()

        return render_template('companyOutput.html', company_list=name_list)

    else:
        try:
            for conpanyId in selected_selected_companys:
                update_sql = "UPDATE company SET status ='rejected' WHERE companyId=%s"                
                cursorReject.execute(update_sql, (conpanyId))
                db_conn.commit()                    

        finally:
            cursorReject.close()

        return render_template('companyOutput.html', company_list=name_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

