from tkinter import E
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
from datetime import date

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
    return render_template('AddEmp.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

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

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/cin", methods=['POST'])
def checkin():
    try:
        emp_id = request.form['emp_id']
        selectSQL = "SELECT * FROM employee WHERE emp_id = "+emp_id
        cursor = db_conn.cursor()
        cursor.execute(selectSQL)
        result = cursor.fetchall()
        if(len(result)!=0):
            querySQL = "INSERT INTO attendance(emp_id, check_in, check_out, payroll) VALUES(%s, %s, '', -1)"
            cursor.execute(querySQL, (emp_id, date.today().strftime("%d-%m-%y")))
            db_conn.commit()
        else:
            print ("<script>alert('No user found!!');</script>")
    except Exception as e :
        return str(e)
    finally:
        cursor.close()
    return render_template('cin.html', empId=emp_id)

@app.route("/cout", methods=['POST'])
def checkout():
    try:
        emp_id = request.form['emp_id']
        selectSQL = "SELECT * FROM employee WHERE emp_id = "+emp_id
        cursor = db_conn.cursor()
        cursor.execute(selectSQL)
        result = cursor.fetchall()
        if(len(result)!=0):
            querySQL = "UPDATE attendance SET check_out = %s WHERE emp_id = %s"
            cursor.execute(querySQL, (date.today().strftime("%d-%m-%y"), emp_id))
            db_conn.commit()
        else:
            print ("<script>alert('No user found!!');</script>")
    except Exception as e :
        return str(e)
    finally:
        cursor.close()
    return render_template('AttendanceEmp.html', empId=emp_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
