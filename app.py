import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session


def get_db_connection():
    return pymysql.connect(host="localhost", user="root", password="", database="tutoring")

app = Flask(__name__)
app.secret_key = "your_secret_key"  

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        connection = get_db_connection()
        cursor = connection.cursor()

        print(f"Attempting login for email: {email}")

        query = "SELECT s_id, email, password FROM student WHERE email = %s"
        cursor.execute(query, (email,))
        student = cursor.fetchone()
        connection.close()

        if student:
            print("User found in the database.")
            stored_password = student[2]

            if stored_password == password:
                session['email'] = email
                session['s_id'] = student[0]
                session['user_id'] = student[0]  
                session['user_name'] = student[1]  
                return redirect(url_for("home1")) 
            else:
                flash("Invalid password", "error")
        else:
            flash("User not found", "error")

    return render_template("login.html")

@app.route("/home1")
def home1():
    if 'user_id' not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("login"))
    
    
    return render_template("home1.html")

@app.route('/logout')
def logout():
    session.pop('user_id', None) 
    session.pop('user_name', None)  
    
    return redirect(url_for('login'))



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_type = request.form.get("user")
        name = request.form.get("name")
        email = request.form.get("email")
        department = request.form.get("department")
        password = request.form.get("password")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if user_type == "Student":
                query = "INSERT INTO student (name, email, department, password) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (name, email, department, password)) 
                
            conn.commit()
            flash("Registration successful!", "success")
            return redirect(url_for("login"))
            
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()
            
    return render_template("register.html")


################################################################################# COURSE STARTS  ######################################

@app.route('/course')
def course():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT course_code, name from course
    """
    cursor.execute(query)
    course = cursor.fetchall()  
    cursor.close()
    conn.close()

    return render_template('course.html', course=course)  


############################################################# TUTOR LIST STARTS ##############################################
@app.route('/tutor')
def tutor():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT tutor.name, tutor.t_id, tutor.d_id, tutor.cgpa, tutor.email, tutor.per_hour_charge, tutor_free_time.free_time, offers.course_code
        FROM tutor
        LEFT JOIN tutor_free_time ON tutor.t_id = tutor_free_time.t_id LEFT JOIN offers ON tutor.t_id=offers.t_id
    """
    cursor.execute(query)
    tutor= cursor.fetchall()  
    cursor.close()
    conn.close()

    return render_template('tutor.html', tutor=tutor)


########################################################################################### Profile STARTS ###########################

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    s_id = session['s_id']
    print(f"Session student_id: {s_id}") 

    if not s_id:
        print("No student is logged in.")
        return redirect(url_for('login'))

    print(f"Fetching profile for student ID: {s_id}")


    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM student WHERE s_id = %s', (s_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    if student:

        if request.method == 'POST':
            name = request.form.get('name')
            department = request.form.get('department')
            email = request.form.get('email')
            password = request.form.get('password')

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE student 
                SET name = %s, department = %s, email = %s,password = %s
                WHERE s_id = %s
            ''', (name, department, email, password, s_id))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Profile updated successfully!", "success")
            return redirect(url_for('profile'))  

        return render_template('profile.html', student=student)
    else:
        flash("Student not found.", "error")
        return redirect(url_for('login'))


@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    s_id = session['s_id']
    if not s_id:
        flash("You must be logged in to delete your profile.", "error")
        return redirect(url_for('login'))

    try:

        conn = get_db_connection()
        cursor = conn.cursor()


        cursor.execute('DELETE FROM student WHERE s_id = %s', (s_id,))
        conn.commit()
        cursor.close()
        conn.close()

        session.clear()
        flash("Your profile has been deleted.", "success")
        return redirect(url_for('login'))

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('profile'))

############################################## AVAILABLE TUTOR PART ###################################

@app.route('/available_tutor/<course_code>', methods=['GET'])
def available_tutor(course_code):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        query = """
            SELECT tutor.name, tutor.t_id, tutor.d_id, tutor.cgpa, tutor.email, tutor.per_hour_charge, 
                   tutor_free_time.free_time, offers.course_code
            FROM tutor
            LEFT JOIN tutor_free_time ON tutor.t_id = tutor_free_time.t_id
            LEFT JOIN offers ON tutor.t_id = offers.t_id
            WHERE offers.course_code = %s
        """
        cursor.execute(query, (course_code,))
        tutors = cursor.fetchall()
    connection.close()
    return render_template('available_tutor.html', course_code=course_code, tutors=tutors)

from flask import jsonify

@app.route('/available_tutor_22301272/<course_code>', methods=['GET'])
def available_tutor_22301320(course_code):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT tutor.name, tutor.t_id, tutor.d_id, tutor.cgpa, tutor.email, tutor.per_hour_charge, 
                   tutor_free_time.free_time, offers.course_code
            FROM tutor
            LEFT JOIN tutor_free_time ON tutor.t_id = tutor_free_time.t_id
            LEFT JOIN offers ON tutor.t_id = offers.t_id
            WHERE offers.course_code = %s
        """
        cursor.execute(query, (course_code,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()


############################################################################## BOOKING ########################################

@app.route('/book_tutor', methods=['POST'])
def book_tutor():
    print("book_tutor route accessed!")  

    if 'email' not in session:
        print("User not logged in")
        return redirect(url_for('login'))

    s_id = session.get('s_id')
    t_id = request.form.get('t_id')

    print(f"Student ID: {s_id}, Tutor ID: {t_id}")

    if not s_id or not t_id:
        print("Missing s_id or t_id")
        return "Invalid request", 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            query = "INSERT INTO book (s_id, t_id) VALUES (%s, %s);"
            cursor.execute(query, (s_id, t_id))
            connection.commit()
            print("Booking inserted into database")
    except Exception as e:
        print(f"Database error: {e}")
        return "Database error", 500
    finally:
        connection.close()

    return redirect(url_for('course'))

@app.route("/booking")
def booking():
    if 's_id' not in session:
        return redirect(url_for('login'))

    s_id = session['s_id']
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        SELECT tutor.name, tutor.per_hour_charge, tutor.t_id, book.booking_date
        FROM tutor join book on tutor.t_id = book.t_id join student on book.s_id = student.s_id where book.s_id = %s;
    """
    cursor.execute(query,(s_id,))
    tutors = cursor.fetchall()
    connection.close()

    return render_template("booking.html", tutors=tutors)

@app.route("/booking_api_22301272", methods=["GET"])
def booking_api_22301272():
    s_id = session.get('s_id')
    print(f"booking_api called with s_id from session: {s_id}")

  
    if not s_id:
        print("No s_id in session, using fallback '22301311'")
        s_id = '22301311'  

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT tutor.name, tutor.per_hour_charge, tutor.t_id, book.booking_date
            FROM tutor 
            JOIN book ON tutor.t_id = book.t_id 
            JOIN student ON book.s_id = student.s_id 
            WHERE book.s_id = %s;
        """
        cursor.execute(query, (s_id,))
        rows = cursor.fetchall()
        print("Rows fetched:", rows)

        if not rows:
            return jsonify({"message": "No bookings found for this student."}), 404

        columns = [desc[0] for desc in cursor.description]
        bookings = [dict(zip(columns, row)) for row in rows]

        return jsonify(bookings)

    except Exception as e:
        print("Error in booking_api:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    app.run(debug=True)
