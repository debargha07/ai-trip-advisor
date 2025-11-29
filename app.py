import os
import sqlite3
import random
import requests
import markdown
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask App Setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "tripadvisor_secret")

DB_NAME = "tripadvisor.db"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ----------- DATABASE CONNECTION -----------
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), DB_NAME)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ----------- HOME PAGE -----------
@app.route('/')
def index():
    conn = get_db_connection()
    dests = conn.execute("SELECT * FROM destinations").fetchall()
    conn.close()
    return render_template('index.html', destinations=dests)


# ----------- SIGNUP -----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                         (username, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except Exception:
            conn.close()
            return render_template('signup.html', error="Username or email already exists.")
    return render_template('signup.html')


# ----------- LOGIN -----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')


# ----------- LOGOUT -----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ----------- DESTINATION DETAILS -----------
@app.route('/destination/<int:dest_id>')
def destination(dest_id):
    conn = get_db_connection()
    dest = conn.execute("SELECT * FROM destinations WHERE id=?", (dest_id,)).fetchone()
    attractions = conn.execute("SELECT * FROM attractions WHERE destination_id=?", (dest_id,)).fetchall()
    hotels = conn.execute("SELECT * FROM hotels WHERE destination_id=?", (dest_id,)).fetchall()
    conn.close()
    return render_template('advisor.html', dest=dest, attractions=attractions, hotels=hotels)


# ----------- AI TRIP PLANNER -----------
@app.route('/advisor/<int:dest_id>', methods=['POST'])
def advisor(dest_id):
    data = request.form
    days = int(data.get('days', 3))
    budget = data.get('budget', 'moderate')
    interests = data.get('interests', '')

    conn = get_db_connection()
    dest = conn.execute("SELECT * FROM destinations WHERE id=?", (dest_id,)).fetchone()
    attractions = conn.execute("SELECT name, description FROM attractions WHERE destination_id=? LIMIT 6", (dest_id,)).fetchall()
    hotels = conn.execute("SELECT name, rating, price_per_night FROM hotels WHERE destination_id=? LIMIT 3", (dest_id,)).fetchall()
    conn.close()

    attractions_text = "\n".join([f"{a['name']}: {a['description']}" for a in attractions])
    hotels_text = "\n".join([f"{h['name']} (₹{h['price_per_night']}/night, rating {h['rating']})" for h in hotels])

    prompt = f"""
You are a professional travel planner. Create a {days}-day itinerary for {dest['city']}, {dest['country']}.
Interests: {interests}. Budget: {budget}.
Attractions:
{attractions_text}
Hotels:
{hotels_text}

Provide a day-by-day detailed itinerary with times, activities, and approximate costs.
"""

    plan_raw = call_openrouter_api(prompt, dest, days)
    plan_html = markdown.markdown(plan_raw, extensions=['extra', 'nl2br'])

    return render_template('advisor_result.html', plan=plan_html, dest=dest)


# ----------- OPENROUTER API CALL -----------
def call_openrouter_api(prompt, dest, days):
    if not OPENROUTER_API_KEY:
        return "(OpenRouter API key not found in .env file)\n\n" + simple_plan_template(dest, days)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourdomain.com",
        "X-Title": "AI Trip Advisor"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a professional travel planner AI."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 800
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers, json=data)
        if response.status_code == 200:
            resp_json = response.json()
            return resp_json['choices'][0]['message']['content']
        else:
            return f"(Error {response.status_code}: {response.text})\n\n" + simple_plan_template(dest, days)
    except Exception as e:
        return f"(API error: {e})\n\n" + simple_plan_template(dest, days)


def simple_plan_template(dest, days):
    plan = [f"Day {i+1}: Explore {dest['city']} and enjoy local attractions." for i in range(days)]
    return "\n".join(plan)


# ----------- BOOK NOW PAGE -----------
@app.route('/book_trip/<int:dest_id>')
def book_trip_page(dest_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    dest = conn.execute("SELECT * FROM destinations WHERE id=?", (dest_id,)).fetchone()
    conn.close()
    return render_template('book_trip.html', dest=dest)


@app.route('/book_trip/<int:dest_id>', methods=['POST'])
def book_trip(dest_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    travellers = request.form.get('travellers', 1)
    amount = int(request.form['amount'])

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO bookings (user_id, booking_type, item_id, start_date, end_date, amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, 'trip', dest_id, start_date, end_date, amount, 'confirmed'))
    conn.commit()
    booking_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    return redirect(url_for('ticket', booking_id=booking_id))


# ----------- MY BOOKINGS -----------
@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    bookings = conn.execute("SELECT * FROM bookings WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    return render_template('my_bookings.html', bookings=bookings)


# ----------- TICKET PAGE -----------
@app.route('/ticket/<int:booking_id>')
def ticket(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    booking = conn.execute("SELECT * FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
    conn.close()
    if not booking:
        return "Booking not found", 404
    ticket_no = random.randint(100000, 999999)
    return render_template('ticket.html', booking=booking, ticket_no=ticket_no)


# ----------- CANCEL BOOKING -----------
@app.route('/cancel/<int:booking_id>', methods=['POST'])
def cancel(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute("UPDATE bookings SET status='cancelled' WHERE booking_id=?", (booking_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('my_bookings'))


# ----------- RUN APP -----------
if __name__ == "__main__":
    app.run(debug=True)
