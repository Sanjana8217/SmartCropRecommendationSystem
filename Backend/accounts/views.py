from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import pickle
from django.shortcuts import render, redirect
from django.http import HttpResponse

import os
import joblib
import requests

from reportlab.pdfgen import canvas
from openpyxl import Workbook

from django.db.models import Count

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required

from .models import CropPrediction, Feedback
from django.db.models import Avg
from django.core.mail import send_mail
from django.conf import settings
# Base Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ML Model Path
model_path = os.path.join(
    BASE_DIR,
    "ml_model",
    "model.pkl"
)

model = joblib.load(model_path)
# Disease Model

disease_model = None

def get_disease_model():
    global disease_model

    if disease_model is None:
        disease_model = load_model(
            os.path.join(BASE_DIR, "disease_model.keras")
        )

    return disease_model

with open(
    os.path.join(BASE_DIR, "class_names.pkl"),
    "rb"
) as f:
    class_names = pickle.load(f)

# OpenWeather API Key
API_KEY = "fb0c8ff306cacc972feea6978d373f07"


def home(request):
    return render(request, "accounts/home.html")


# =========================
# LOGIN
# =========================
def login(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            auth_login(request, user)
            return redirect("/crop/")

        return render(
            request,
            "accounts/login.html",
            {
                "error": "Invalid Username or Password"
            }
        )

    return render(request, "accounts/login.html")


# =========================
# REGISTER
# =========================
def register(request):

    if request.method == "POST":

        fullname = request.POST["fullname"]
        email = request.POST["email"]
        username = request.POST["username"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password != confirm_password:

            return render(
                request,
                "accounts/register.html",
                {
                    "error": "Passwords do not match"
                }
            )

        if User.objects.filter(username=username).exists():

            return render(
                request,
                "accounts/register.html",
                {
                    "error": "Username already exists"
                }
            )

        User.objects.create_user(
            first_name=fullname,
            email=email,
            username=username,
            password=password
        )

        return render(
            request,
            "accounts/register.html",
            {
                "success": "Registration Successful. Please Login."
            }
        )

    return render(request, "accounts/register.html")


# =========================
# LOGOUT
# =========================
def logout_user(request):

    logout(request)

    return redirect("/login/")


# =========================
# CROP PREDICTION
# =========================
@login_required(login_url="/login/")
def crop(request):

    result = ""
    fertilizer = ""
    crop_image = ""
    crop_info = {}
    temperature = ""
    humidity = ""
    estimated_yield = ""
    forecast_data = []

    if request.method == "POST":

        N = float(request.POST["N"])
        P = float(request.POST["P"])
        K = float(request.POST["K"])
        city = request.POST["city"]

        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&appid={API_KEY}&units=metric"
        )

        weather_data = requests.get(weather_url).json()

        if "main" not in weather_data:

            return render(
                request,
                "accounts/crop.html",
                {
                    "error": "Invalid city name. Please enter a valid city."
                }
            )

        temperature = weather_data["main"]["temp"]
        humidity = weather_data["main"]["humidity"]

        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?"
            f"q={city}&appid={API_KEY}&units=metric"
        )

        forecast_response = requests.get(forecast_url).json()

        if "list" in forecast_response:

            for item in forecast_response["list"][:7]:

                forecast_data.append({
                    "date": item["dt_txt"],
                    "temp": item["main"]["temp"]
                })

        ph = float(request.POST["ph"])
        rainfall = float(request.POST["rainfall"])

        prediction = model.predict([
            [
                N,
                P,
                K,
                temperature,
                humidity,
                ph,
                rainfall
            ]
        ])

        result = prediction[0]

        crop_image = result.lower() + ".jpg"

        fertilizer = "General Organic Fertilizer"

        crop_details = {
            "coffee": {
                "season": "Monsoon",
                "soil": "Rich Loamy Soil",
                "water": "Medium",
                "duration": "3 Years"
            },
            "rice": {
                "season": "Kharif",
                "soil": "Clay Loam",
                "water": "High",
                "duration": "120 Days"
            },
            "maize": {
                "season": "Kharif",
                "soil": "Well Drained",
                "water": "Medium",
                "duration": "90 Days"
            },
            "wheat": {
                "season": "Rabi",
                "soil": "Loamy Soil",
                "water": "Medium",
                "duration": "140 Days"
            }
        }

        crop_info = crop_details.get(
            result.lower(),
            {
                "season": "Suitable Season",
                "soil": "Good Fertile Soil",
                "water": "Moderate",
                "duration": "Depends on Crop"
            }
        )

        yield_data = {
            "rice": "4.8 Tons/Acre",
            "wheat": "3.5 Tons/Acre",
            "maize": "5.2 Tons/Acre",
            "banana": "18 Tons/Acre",
            "cotton": "2.4 Tons/Acre",
            "coffee": "2.1 Tons/Acre",
            "mango": "8 Tons/Acre",
            "orange": "10 Tons/Acre"
        }

        estimated_yield = yield_data.get(
            result.lower(),
            "Data Not Available"
        )

        CropPrediction.objects.create(
            user=request.user,
            nitrogen=N,
            phosphorus=P,
            potassium=K,
            temperature=temperature,
            humidity=humidity,
            ph=ph,
            rainfall=rainfall,
            crop=result,
            fertilizer=fertilizer
        )
        send_mail(
    subject="Smart Crop Recommendation Result",
    message=f"""
Recommended Crop : {result}

Suggested Fertilizer : {fertilizer}

Temperature : {temperature} °C
Humidity : {humidity} %

Estimated Yield : {estimated_yield}
""",
    from_email=settings.EMAIL_HOST_USER,
    recipient_list=[request.user.email],
    fail_silently=False,
)

    return render(
        request,
        "accounts/crop.html",
        {
            "result": result,
            "fertilizer": fertilizer,
            "crop_image": crop_image,
            "crop_info": crop_info,
            "temperature": temperature,
            "humidity": humidity,
            "estimated_yield": estimated_yield,
            "forecast_data": forecast_data,
        }
    )


@login_required(login_url="/login/")
def history(request):

    predictions = CropPrediction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "accounts/history.html",
        {
            "predictions": predictions
        }
    )


@login_required(login_url="/login/")
def delete_prediction(request, id):

    prediction = CropPrediction.objects.get(
        id=id,
        user=request.user
    )

    prediction.delete()

    return redirect("/history/")


@login_required(login_url="/login/")
def download_report(request):

    prediction = CropPrediction.objects.latest("created_at")

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="crop_report.pdf"'
    )

    pdf = canvas.Canvas(response)

    pdf.drawString(100, 800, "Smart Crop Recommendation Report")
    pdf.drawString(100, 760, f"Crop: {prediction.crop}")
    pdf.drawString(100, 730, f"Fertilizer: {prediction.fertilizer}")
    pdf.drawString(100, 700, f"Nitrogen: {prediction.nitrogen}")
    pdf.drawString(100, 670, f"Phosphorus: {prediction.phosphorus}")
    pdf.drawString(100, 640, f"Potassium: {prediction.potassium}")
    pdf.drawString(100, 610, f"Temperature: {prediction.temperature}")
    pdf.drawString(100, 580, f"Humidity: {prediction.humidity}")
    pdf.drawString(100, 550, f"pH: {prediction.ph}")
    pdf.drawString(100, 520, f"Rainfall: {prediction.rainfall}")

    pdf.save()

    return response


@login_required(login_url="/login/")
@login_required(login_url="/login/")
def dashboard(request):

    total_predictions = CropPrediction.objects.count()

    latest_prediction = CropPrediction.objects.last()

    crop_stats = (
        CropPrediction.objects
        .values("crop")
        .annotate(count=Count("crop"))
        .order_by("-count")
    )

    most_predicted_crop = None

    if crop_stats:
        most_predicted_crop = crop_stats[0]["crop"]

    crop_names = [item["crop"] for item in crop_stats]

    crop_counts = [item["count"] for item in crop_stats]

    total_crop_types = len(crop_names)

    # Feedback Statistics
    total_feedbacks = Feedback.objects.count()

    avg_rating = Feedback.objects.aggregate(
        Avg("rating")
    )["rating__avg"]

    if avg_rating is None:
        avg_rating = 0

    return render(
        request,
        "accounts/dashboard.html",
        {
            "total_predictions": total_predictions,
            "latest_prediction": latest_prediction,
            "most_predicted_crop": most_predicted_crop,
            "crop_names": crop_names,
            "crop_counts": crop_counts,
            "total_crop_types": total_crop_types,

            # Feedback Data
            "total_feedbacks": total_feedbacks,
            "avg_rating": round(avg_rating, 2),
        }
    )

@login_required(login_url="/login/")
def export_excel(request):

    workbook = Workbook()

    sheet = workbook.active
    sheet.title = "Crop Predictions"

    sheet.append([
        "Crop",
        "Fertilizer",
        "Nitrogen",
        "Phosphorus",
        "Potassium",
        "Temperature",
        "Humidity",
        "pH",
        "Rainfall"
    ])

    predictions = CropPrediction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    for p in predictions:

        sheet.append([
            p.crop,
            p.fertilizer,
            p.nitrogen,
            p.phosphorus,
            p.potassium,
            p.temperature,
            p.humidity,
            p.ph,
            p.rainfall
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        'attachment; filename="crop_predictions.xlsx"'
    )

    workbook.save(response)

    return response
@login_required(login_url="/login/")
def disease_detection(request):

    prediction = ""
    treatment = ""

    if request.method == "POST":

        uploaded_file = request.FILES["leaf_image"]

        temp_path = os.path.join(
            BASE_DIR,
            "temp_leaf.jpg"
        )

        with open(temp_path, "wb+") as destination:

            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        img = image.load_img(
            temp_path,
            target_size=(128, 128)
        )

        img_array = image.img_to_array(img)

        img_array = img_array / 255.0

        img_array = np.expand_dims(
            img_array,
            axis=0
        )

        model = get_disease_model()

        result = model.predict(img_array)
        
        disease_class = class_names[np.argmax(result)]

        disease_info = {

            "Tomato_healthy": {
                "name": "Tomato - Healthy Plant",
                "treatment": "No disease detected. Continue regular watering and monitoring."
            },

            "Tomato_Early_blight": {
                "name": "Tomato - Early Blight",
                "treatment": "Remove infected leaves and apply Mancozeb fungicide."
            },

            "Tomato_Late_blight": {
                "name": "Tomato - Late Blight",
                "treatment": "Use Copper fungicide and improve air circulation."
            },

            "Tomato_Leaf_Mold": {
                "name": "Tomato - Leaf Mold",
                "treatment": "Reduce humidity and use suitable fungicide spray."
            },

            "Tomato_Bacterial_spot": {
                "name": "Tomato - Bacterial Spot",
                "treatment": "Remove infected leaves and use copper-based bactericide."
            },

            "Tomato_Septoria_leaf_spot": {
                "name": "Tomato - Septoria Leaf Spot",
                "treatment": "Apply fungicide and avoid overhead watering."
            },

            "Tomato_Spider_mites_Two_spotted_spider_mite": {
                "name": "Tomato - Spider Mites",
                "treatment": "Spray neem oil or miticide."
            },

            "Tomato__Target_Spot": {
                "name": "Tomato - Target Spot",
                "treatment": "Use fungicide and remove infected foliage."
            },

            "Tomato__Tomato_mosaic_virus": {
                "name": "Tomato - Mosaic Virus",
                "treatment": "Remove infected plants immediately."
            },

            "Tomato__Tomato_YellowLeaf__Curl_Virus": {
                "name": "Tomato - Yellow Leaf Curl Virus",
                "treatment": "Control whiteflies and remove infected plants."
            },

            "Potato___Early_blight": {
                "name": "Potato - Early Blight",
                "treatment": "Apply fungicide and remove affected leaves."
            },

            "Potato___Late_blight": {
                "name": "Potato - Late Blight",
                "treatment": "Apply copper fungicide and improve drainage."
            },

            "Potato___healthy": {
                "name": "Potato - Healthy Plant",
                "treatment": "No disease detected."
            },

            "Pepper__bell___Bacterial_spot": {
                "name": "Pepper Bell - Bacterial Spot",
                "treatment": "Use copper bactericide and remove infected leaves."
            },

            "Pepper__bell___healthy": {
                "name": "Pepper Bell - Healthy Plant",
                "treatment": "No disease detected."
            }
        }

        prediction = disease_info.get(
            disease_class,
            {
                "name": disease_class,
                "treatment": "No recommendation available."
            }
        )["name"]

        treatment = disease_info.get(
            disease_class,
            {
                "name": disease_class,
                "treatment": "No recommendation available."
            }
        )["treatment"]

    return render(
        request,
        "accounts/disease.html",
        {
            "prediction": prediction,
            "treatment": treatment
        }
    )
@login_required(login_url="/login/")
def feedback(request):

    message = ""

    if request.method == "POST":

        rating = request.POST["rating"]

        user_feedback = request.POST["feedback"]

        Feedback.objects.create(
            user=request.user,
            rating=rating,
            feedback=user_feedback
        )

        message = "Thank you for your feedback!"

    return render(
        request,
        "accounts/feedback.html",
        {
            "message": message
        }
    )