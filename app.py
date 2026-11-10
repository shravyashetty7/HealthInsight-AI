import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

load_dotenv()

from models import db, Patient
from validation import validate_patient
from ai_service import generate_health_remarks

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "development-only-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///healthinsight.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# One worker avoids flooding the API and keeps the web request fast.
ai_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="healthinsight-ai")
PENDING_REMARKS = "AI remarks are being generated..."


def form_values():
    return {
        "full_name": request.form.get("full_name", ""),
        "date_of_birth": request.form.get("date_of_birth", ""),
        "email": request.form.get("email", ""),
        "glucose": request.form.get("glucose", ""),
        "haemoglobin": request.form.get("haemoglobin", ""),
        "cholesterol": request.form.get("cholesterol", ""),
    }


def _generate_remarks_for_patient(patient_id, values):
    """Run Gemini outside the request, using a fresh SQLAlchemy app context."""
    with app.app_context():
        try:
            remarks = generate_health_remarks(values)
            patient = db.session.get(Patient, patient_id)
            if patient is not None:
                patient.remarks = remarks
                db.session.commit()
        except Exception as error:
            db.session.rollback()
            print(f"Background AI generation error for patient {patient_id}: {error}")
        finally:
            db.session.remove()


def queue_ai_remarks(patient_id, values):
    ai_executor.submit(_generate_remarks_for_patient, patient_id, dict(values))


@app.route("/")
def dashboard():
    patients = Patient.query.order_by(Patient.id.desc()).all()
    return render_template("dashboard.html", patients=patients, total=len(patients), today=date.today())


@app.route("/patients")
def patient_list():
    patients = Patient.query.order_by(Patient.id.desc()).all()
    return render_template("patients.html", patients=patients, pending_remarks=PENDING_REMARKS)


@app.route("/patients/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        data = form_values()
        errors, parsed_dob, values = validate_patient(data)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_patient.html", data=data), 400

        patient = Patient(
            full_name=data["full_name"].strip(),
            date_of_birth=parsed_dob,
            email=data["email"].strip(),
            glucose=values["glucose"],
            haemoglobin=values["haemoglobin"],
            cholesterol=values["cholesterol"],
            remarks=PENDING_REMARKS,
        )
        db.session.add(patient)
        db.session.commit()  # Save first; never wait for Gemini during CRUD.
        queue_ai_remarks(patient.id, values)
        flash("Patient record created successfully. AI remarks are being generated separately.", "success")
        return redirect(url_for("patient_list"))

    return render_template("add_patient.html", data={})


@app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
def edit_patient(patient_id):
    patient = db.get_or_404(Patient, patient_id)
    if request.method == "POST":
        data = form_values()
        errors, parsed_dob, values = validate_patient(data)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("edit_patient.html", patient=patient, data=data), 400

        patient.full_name = data["full_name"].strip()
        patient.date_of_birth = parsed_dob
        patient.email = data["email"].strip()
        patient.glucose = values["glucose"]
        patient.haemoglobin = values["haemoglobin"]
        patient.cholesterol = values["cholesterol"]
        patient.remarks = PENDING_REMARKS
        db.session.commit()
        queue_ai_remarks(patient.id, values)
        flash("Patient record updated successfully. AI remarks are being generated separately.", "success")
        return redirect(url_for("patient_list"))

    data = {
        "full_name": patient.full_name,
        "date_of_birth": patient.date_of_birth.strftime("%d/%m/%Y"),
        "email": patient.email,
        "glucose": patient.glucose,
        "haemoglobin": patient.haemoglobin,
        "cholesterol": patient.cholesterol,
    }
    return render_template("edit_patient.html", patient=patient, data=data)


@app.get("/patients/<int:patient_id>/remarks-status")
def remarks_status(patient_id):
    patient = db.get_or_404(Patient, patient_id)
    remarks = patient.remarks or "Not generated"
    return jsonify({"remarks": remarks, "pending": remarks == PENDING_REMARKS})


@app.post("/patients/<int:patient_id>/delete")
def delete_patient(patient_id):
    patient = db.get_or_404(Patient, patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash("Patient record deleted.", "success")
    return redirect(url_for("patient_list"))


@app.get("/health")
def health_check():
    return {"status": "ok", "application": "HealthInsight"}


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
