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
        try:
            query = "SELECT s_id, email, password,department FROM student WHERE email = %s"
            cursor.execute(query, (email,))
            student = cursor.fetchone()


            if student:
                print("User found in the database.")
                stored_password = student[2]


                if stored_password == password:
                    session['role'] = "student"
                    session['email'] = email
                    session['s_id'] = student[0]
                    session['user_id'] = student[0]  
                    session['user_name'] = student[1]
                    session['dept'] = student[3]
                    return redirect(url_for("home1"))
                else:
                    flash("Invalid password", "error")
                    return render_template("login.html")
            else:
                query = "SELECT t_id, name, email, password, department, per_hour_charge, available_slot FROM tutor WHERE email = %s "
                cursor.execute(query,(email,))
                tutor = cursor.fetchone()
                if tutor:
                    t_id, t_name, t_email, t_pass, t_dept,t_per_hour_charge, t_available_slot = tutor
                    if t_pass == password:
                        session["role"] = "tutor"
                        session["email"] = t_email
                        session["t_id"] = t_id
                        session["user_id"] = t_id
                        session["user_name"] = t_name
                        session["dept"] = t_dept
                        session['per_hour_charge'] = t_per_hour_charge
                        session["available_slot"] = t_available_slot
                        return redirect(url_for("tutor_home"))
                    else:
                        flash("Invalid password", "error")
                        return render_template("login.html")
        finally:
            cursor.close()
            connection.close()


    return render_template("login.html")


@app.route("/tutor_home")
def tutor_home():
    if 'user_id' not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("login"))
    return render_template("tutor_home.html")


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
        user_type      = request.form.get("user")
        name           = request.form.get("name")
        email          = request.form.get("email")
        department     = request.form.get("department")
        password       = request.form.get("password")
        cgpa_raw       = (request.form.get("cgpa") or "").strip()
        charge_raw     = (request.form.get("charge") or "").strip()
        available_slot = (request.form.get("available_slot") or "").strip()
        offered_raw    = (request.form.get("offered_courses") or "").strip()


        conn = get_db_connection()
        cursor = conn.cursor()


        try:
            if user_type == "Student":
                cursor.execute(
                    """
                    INSERT INTO student (name, email, department, password)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (name, email, department, password)
                )


            elif user_type == "Tutor":
                if not all([cgpa_raw, charge_raw, available_slot]):
                    flash("CGPA, Charge, and Available Slot are required for teachers.", "error")
                    return render_template("register.html")


                try:
                    cgpa = float(cgpa_raw)
                    charge = float(charge_raw)
                except ValueError:
                    flash("Invalid CGPA or Charge value.", "error")
                    return render_template("register.html")


                cursor.execute(
                    """
                    INSERT INTO tutor (name, email, department, password, cgpa, per_hour_charge, available_slot)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (name, email, department, password, cgpa, charge, available_slot)
                )


                t_id = cursor.lastrowid


                if not t_id:
                    cursor.execute("SELECT t_id FROM tutor WHERE email = %s ORDER BY t_id DESC LIMIT 1", (email,))
                    row = cursor.fetchone()
                    if not row:
                        raise Exception("Could not retrieve tutor id after insert.")
                    t_id = row[0]


                if offered_raw:
                    courses = [c.strip() for c in offered_raw.split(",") if c.strip()]
                    seen = set()
                    courses = [c for c in courses if not (c in seen or seen.add(c))]
                    if courses:
                        cursor.executemany(
                            "INSERT INTO offers (t_id, course_code) VALUES (%s, %s)",
                            [(t_id, oc) for oc in courses]
                        )


            else:
                flash("Unknown user type.", "error")
                return render_template("register.html")


            conn.commit()
            flash("Registration successful!", "success")
            return redirect(url_for("login"))


        except Exception as e:
            conn.rollback()
            flash(f"Registration failed: {str(e)}", "error")
            return render_template("register.html")
        finally:
            cursor.close()
            conn.close()


    return render_template("register.html")










@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if session["role"] == "student":
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




    elif session["role"] == "tutor":
        t_id = session['t_id']
        print(f"Session student_id: {t_id}")


        if not t_id:
            print("No student is logged in.")
            return redirect(url_for('login'))


        print(f"Fetching profile for student ID: {t_id}")


        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tutor WHERE t_id = %s', (t_id,))
        tutor = cursor.fetchone()
        cursor.close()
        conn.close()
        if tutor:
            if request.method == 'POST':
                name = request.form.get('name')
                department = request.form.get('department')
                email = request.form.get('email')
                password = request.form.get('password')
                cgpa = request.form.get('cgpa')
                per_hour_charge = request.form.get('per_hour_charge')
                available_slot = request.form.get('available_slot')


                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tutor
                    SET name = %s, department = %s, email = %s,password = %s, cgpa = %s, per_hour_charge = %s,available_slot = %s
                    WHERE t_id = %s
                ''', (name, department, email, password, cgpa, per_hour_charge, available_slot, t_id))
                conn.commit()
                cursor.close()
                conn.close()


                flash("Profile updated successfully!", "success")
                return redirect(url_for('profile'))
            return render_template('profile.html', tutor=tutor)
        else:
            flash("Student not found.", "error")
            return redirect(url_for('login'))








@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    if session["role"] == "student":
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
   
    elif session["role"] == "tutor":
        t_id = session['t_id']
        if not t_id:
            flash("You must be logged in to delete your profile.", "error")
            return redirect(url_for('login'))


        try:


            conn = get_db_connection()
            cursor = conn.cursor()




            cursor.execute('DELETE FROM tutor WHERE t_id = %s', (t_id,))
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

@app.route('/dept')
def dept():
    return render_template("dept.html")

if __name__ == "__main__":
    app.run(debug=True)
