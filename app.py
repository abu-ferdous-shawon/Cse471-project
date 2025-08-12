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

#a

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





if __name__ == "__main__":
    app.run(debug=True)
