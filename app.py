import datetime
import os
import sqlite3

from flask import Flask, session, render_template, redirect, request, g, make_response

from config import Config
from database import DataBase

app = Flask(__name__)
app.config.from_object(Config)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'database.db')))
app.permanent_session_lifetime = datetime.timedelta(days=15)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
        return g.link_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "link_db"):
        g.link_db.close()


@app.route("/", methods=["GET"])
def main():
    return render_template("main.html", user=session.get("id", None), none=None)


@app.route("/standard_deduction", methods=["GET", "POST"])
def standard_deduction():
    deduction = None
    if request.method == "POST":
        form = request.form
        children = int(form["field2"])
        if children <= 2:
            children *= 1400
        else:
            children = 2800 + (children - 2) * 3_000
        deduction = max(int(form["field1"]) - children, 0) * .13

        if session.get("id", None) is None:
            session["id"] = DataBase().create_user()
        DataBase().add_deduction(deduction, form["type"], session["id"], form["field1"], form["field2"])

    return render_template("standard_deduction.html", deduction=deduction, user=session.get("id", None), none=None)


@app.route("/social_deduction", methods=["GET", "POST"])
def social_deduction():
    donation = None
    education = None
    medicine = None
    deduction = None
    if request.method == "POST":
        form = request.form
        deduction_type = form["type"]
        if deduction_type == "Вычет за лечение":
            medicine = (int(form["field1"]) - min(50_000, int(form["field2"]))) * 0.13
            deduction = medicine
        elif deduction_type == "Вычет за обучение":
            education = (int(form["field1"]) - min(50_000, int(form["field2"]))) * 0.13
            deduction = education
        elif deduction_type == "Вычет за пожертвования":
            donation = (int(form["field1"]) - min(int(form["field1"]) * 0.25, int(form["field2"]))) * 0.13
            deduction = donation

        if session.get("id", None) is None:
            session["id"] = DataBase().create_user()
        DataBase().add_deduction(deduction, form["type"], session["id"], form["field1"], form["field2"])

    return render_template("social_deduction.html",
                           donation=donation,
                           education=education,
                           medicine=medicine,
                           user=session.get("id", None),
                           none=None, )


@app.route("/property_deduction", methods=["GET", "POST"])
def property_deduction():
    donation = None
    if request.method == "POST":
        form = request.form
        donation = (max(0, int(form["field1"]) - 1_000_000)) * 0.13
        deduction = donation

        if session.get("id", None) is None:
            session["id"] = DataBase().create_user()
        DataBase().add_deduction(deduction, form["type"], session["id"], form["field1"], form["field2"])

    return render_template("property_deduction.html",
                           donation=donation,
                           user=session.get("id", None),
                           none=None, )


@app.route("/other", methods=["GET", "POST"])
def other():
    donation = None
    if request.method == "POST":
        form = request.form
        donation = (int(form["field1"]) - min(int(form["field2"]), 4000)) * 0.13
        deduction = donation

        if session.get("id", None) is None:
            session["id"] = DataBase().create_user()
        DataBase().add_deduction(deduction, form["type"], session["id"], form["field1"], form["field2"])

    return render_template("other.html",
                           donation=donation,
                           user=session.get("id", None),
                           none=None, )


@app.route('/download')
def download_file():
    if session.get("id", None) is None: return redirect("/")
    try:
        file_contents = ""
        deductions = DataBase().get_deductions(session["id"])
        for deduction in deductions:
            text = '"' + str(deduction.time) + '","' + str(deduction.type) + '","'
            if deduction.type == "Вычет за детей":
                text += "Заработная плата: " + deduction.fields[0] + '","' + "Количество детей: " + deduction.fields[1] + '","'
            elif deduction.type == "Вычет за пожертвования":
                text += "Сумма дохода: " + deduction.fields[0] + '","' + "Сумма пожертвования: " + deduction.fields[1] + '","'
            elif deduction.type == "Вычет за обучение":
                text += "Сумма дохода: " + deduction.fields[0] + '","' + "Стоимость обучения: " + deduction.fields[1] + '","'
            elif deduction.type == "Вычет за лечение":
                text += "Сумма дохода: " + deduction.fields[0] + '","' + "Стоимость лечения: " + deduction.fields[1] + '","'
            elif deduction.type == "Имущественный вычет":
                text += "Сумма дохода (нарастающая с момента продажи): " + deduction.fields[0] + '","'
            elif deduction.type == "Доходы, не подлежащие налогообложению":
                text += "Заработная плата: " + deduction.fields[0] + '","' + "Материальная выплата:" + deduction.fields[1] + '","'
            text += "Рассчитанный НДФЛ: " + deduction.deduction
            file_contents += text + '"\n'

        response = make_response(file_contents)
        response.headers.set('Content-Disposition', 'attachment', filename='deductions.csv')
        response.headers.set('Content-Type', 'text/plain')

        return response
    except Exception as e:
        print(e)
        return redirect("/")


@app.errorhandler(404)
def page_not_found(error):
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)
