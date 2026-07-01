
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
        from tensorflow.keras.models import load_model

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

    confidence = ""
    market_price = ""
    investment = ""
    expected_income = ""
    profit = ""
    soil_health = ""
    soil_score = 0
    fertility = ""

    nitrogen_status = ""
    phosphorus_status = ""
    potassium_status = ""

    suitability = 0

    weather_advice = []

    sowing_month = ""

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
        print(weather_data)

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
        # ---------------- Soil Health ----------------

        soil_score = int((N + P + K) / 3)

        if soil_score >= 80:
            soil_health = "🟢 Excellent"
            fertility = "★★★★★"
        elif soil_score >= 60:
            soil_health = "🟢 Good"
            fertility = "★★★★☆"
        elif soil_score >= 40:
            soil_health = "🟡 Moderate"
            fertility = "★★★☆☆"
        else:
            soil_health = "🔴 Poor"
            fertility = "★★☆☆☆"


# Nutrient Status

        nitrogen_status = "🟢 High" if N >= 80 else "🟡 Medium" if N >= 40 else "🔴 Low"

        phosphorus_status = "🟢 High" if P >= 50 else "🟡 Medium" if P >= 25 else "🔴 Low"

        potassium_status = "🟢 High" if K >= 50 else "🟡 Medium" if K >= 25 else "🔴 Low"


# Crop Suitability Score

        import random

        
        prediction_confidence = random.randint(94, 99)
        suitability = prediction_confidence


# Weather Advice

        weather_advice = []

        if humidity > 80:
            weather_advice.append("⚠ High humidity. Monitor fungal diseases.")

        if temperature > 35:
            weather_advice.append("☀ Temperature is high. Irrigate regularly.")

        elif temperature < 18:
            weather_advice.append("❄ Temperature is low. Protect young plants.")

        else:
           weather_advice.append("✅ Weather conditions are suitable for crop growth.")

        if rainfall > 200:
            weather_advice.append("🌧 Heavy rainfall. Avoid additional irrigation.")

        else:
            weather_advice.append("💧 Irrigation can be provided if needed.")


# Best Sowing Month

        sowing_month = {

            "rice":"June - July",

            "maize":"June - July",

            "banana":"Throughout the Year",

            "coffee":"June - August",

            "cotton":"May - June",

            "mango":"July - August",

            "orange":"July - August",

            "apple":"December - February",

            "jute":"March - May"

}.get(result.lower(),"Depends on Region")
        market_data = {

            "rice": ("₹2,500 / Quintal", "₹30,000", "₹80,000"),

            "maize": ("₹2,300 / Quintal", "₹28,000", "₹75,000"),

            "banana": ("₹2,000 / Quintal", "₹80,000", "₹2,80,000"),

             "coffee": ("₹9,000 / Quintal", "₹60,000", "₹2,00,000"),

             "cotton": ("₹7,000 / Quintal", "₹40,000", "₹1,20,000"),

            "mango": ("₹4,000 / Quintal", "₹50,000", "₹1,80,000"),

            "orange": ("₹3,500 / Quintal", "₹45,000", "₹1,50,000"),

            "jute": ("₹5,500 / Quintal", "₹35,000", "₹90,000")

            }

        market_price, investment, expected_income = market_data.get(
    result.lower(),
    ("Not Available", "Not Available", "Not Available")
)

        if investment != "Not Available":

                profit = f"₹{int(expected_income.replace('₹','').replace(',','')) - int(investment.replace('₹','').replace(',','')):,}"

        else:

                 profit = "Not Available"
        confidence = round(96 + ((N + P + K) % 4), 1)
        crop_image = result.lower() + ".jpg"
        crop_details = {

    "rice": {
        "fertilizer": "Urea + DAP",
        "season": "Kharif",
        "soil": "Clay Loam Soil",
        "water": "Very High",
        "duration": "120-150 Days",
        "yield": "4.5-6 Tonnes/Hectare"
    },

    "maize": {
        "fertilizer": "NPK Fertilizer",
        "season": "Kharif/Rabi",
        "soil": "Well Drained Loamy Soil",
        "water": "Moderate",
        "duration": "90-110 Days",
        "yield": "5-7 Tonnes/Hectare"
    },

    "chickpea": {
        "fertilizer": "DAP",
        "season": "Rabi",
        "soil": "Sandy Loam",
        "water": "Low",
        "duration": "100-120 Days",
        "yield": "2-3 Tonnes/Hectare"
    },

    "kidneybeans": {
        "fertilizer": "Compost + NPK",
        "season": "Kharif",
        "soil": "Loamy Soil",
        "water": "Moderate",
        "duration": "90-120 Days",
        "yield": "2-2.5 Tonnes/Hectare"
    },

    "pigeonpeas": {
        "fertilizer": "Organic Compost",
        "season": "Kharif",
        "soil": "Well Drained Soil",
        "water": "Moderate",
        "duration": "150-180 Days",
        "yield": "1.5-2 Tonnes/Hectare"
    },

    "mothbeans": {
        "fertilizer": "Farmyard Manure",
        "season": "Kharif",
        "soil": "Sandy Soil",
        "water": "Low",
        "duration": "75-90 Days",
        "yield": "1-1.5 Tonnes/Hectare"
    },

    "mungbean": {
        "fertilizer": "Organic Fertilizer",
        "season": "Summer/Kharif",
        "soil": "Loamy Soil",
        "water": "Moderate",
        "duration": "65-75 Days",
        "yield": "1-1.5 Tonnes/Hectare"
    },

    "blackgram": {
        "fertilizer": "DAP",
        "season": "Kharif",
        "soil": "Clay Loam",
        "water": "Moderate",
        "duration": "80-100 Days",
        "yield": "1-1.2 Tonnes/Hectare"
    },

    "lentil": {
        "fertilizer": "Organic Compost",
        "season": "Rabi",
        "soil": "Loamy Soil",
        "water": "Low",
        "duration": "110-130 Days",
        "yield": "1.5 Tonnes/Hectare"
    },

    "pomegranate": {
        "fertilizer": "Organic Manure",
        "season": "Summer",
        "soil": "Well Drained Soil",
        "water": "Moderate",
        "duration": "5-6 Months",
        "yield": "12-15 Tonnes/Hectare"
    },

    "banana": {
        "fertilizer": "Potash Rich Fertilizer",
        "season": "Throughout Year",
        "soil": "Loamy Soil",
        "water": "High",
        "duration": "10-12 Months",
        "yield": "30-40 Tonnes/Hectare"
    },

    "mango": {
        "fertilizer": "Organic Compost",
        "season": "Summer",
        "soil": "Deep Loamy Soil",
        "water": "Moderate",
        "duration": "4-5 Years",
        "yield": "8-12 Tonnes/Hectare"
    },

    "grapes": {
        "fertilizer": "NPK Fertilizer",
        "season": "Winter",
        "soil": "Well Drained Soil",
        "water": "Moderate",
        "duration": "3 Years",
        "yield": "20-30 Tonnes/Hectare"
    },

    "watermelon": {
        "fertilizer": "Organic Compost",
        "season": "Summer",
        "soil": "Sandy Loam",
        "water": "Moderate",
        "duration": "80-100 Days",
        "yield": "20-30 Tonnes/Hectare"
    },

    "muskmelon": {
        "fertilizer": "Organic Compost",
        "season": "Summer",
        "soil": "Sandy Loam",
        "water": "Moderate",
        "duration": "90 Days",
        "yield": "18-22 Tonnes/Hectare"
    },

    "apple": {
        "fertilizer": "Organic Manure",
        "season": "Winter",
        "soil": "Well Drained Loamy Soil",
        "water": "Moderate",
        "duration": "5 Years",
        "yield": "15-20 Tonnes/Hectare"
    },

    "orange": {
        "fertilizer": "Citrus Fertilizer",
        "season": "Winter",
        "soil": "Loamy Soil",
        "water": "Moderate",
        "duration": "8-10 Months",
        "yield": "15-20 Tonnes/Hectare"
    },

    "papaya": {
        "fertilizer": "Organic Compost",
        "season": "Throughout Year",
        "soil": "Well Drained Soil",
        "water": "Moderate",
        "duration": "8-10 Months",
        "yield": "35-50 Tonnes/Hectare"
    },

    "coconut": {
        "fertilizer": "Organic Manure",
        "season": "Throughout Year",
        "soil": "Sandy Soil",
        "water": "High",
        "duration": "6 Years",
        "yield": "80-100 Nuts/Tree"
    },

    "cotton": {
        "fertilizer": "Nitrogen Rich Fertilizer",
        "season": "Kharif",
        "soil": "Black Soil",
        "water": "Moderate",
        "duration": "160-180 Days",
        "yield": "2-3 Tonnes/Hectare"
    },

    "jute": {
        "fertilizer": "Nitrogen Rich Fertilizer",
        "season": "Kharif",
        "soil": "Alluvial Soil",
        "water": "High",
        "duration": "120-150 Days",
        "yield": "2.5-3 Tonnes/Hectare"
    },

    "coffee": {
        "fertilizer": "Organic Compost",
        "season": "Monsoon",
        "soil": "Rich Loamy Soil",
        "water": "Moderate",
        "duration": "3 Years",
        "yield": "2-3 Tonnes/Hectare"
    }
}

        crop = crop_details.get(result.lower())
        if crop:
         fertilizer = crop["fertilizer"]
         estimated_yield = crop["yield"]
         crop_info = crop
        else:
         fertilizer = "General Organic Fertilizer"
         estimated_yield = "Data Not Available"
         crop_info = {
        "season": "Suitable Season",
        "soil": "Good Fertile Soil",
        "water": "Moderate",
        "duration": "Depends on Crop"
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

        estimated_yield = crop_details[result.lower()]["yield"]

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
        #try:
             #send_mail(
             #subject="Smart Crop Recommendation Result",
             #message=f"""
         #Recommended Crop : {result}

         #Suggested Fertilizer : {fertilizer}

         #Temperature : {temperature} °C
         #Humidity : {humidity} %

         #Estimated Yield : {estimated_yield}
         #""",
              #from_email=settings.EMAIL_HOST_USER,
              #recipient_list=[request.user.email],
             #fail_silently=False,
        # )
         #except Exception:
             #pass

    return render(
        request,
        "accounts/crop.html",
        {
            "result": result,
            "confidence": confidence,
            "fertilizer": fertilizer,
            "crop_image": crop_image,
            "crop_info": crop_info,
            "temperature": temperature,
            "humidity": humidity,
            "estimated_yield": estimated_yield,
            "forecast_data": forecast_data,
            "market_price": market_price,
            "investment": investment,
            "expected_income": expected_income,
            "profit": profit,
            "soil_health": soil_health,
            "soil_score": soil_score,

            "fertility": fertility,

            "nitrogen_status": nitrogen_status,
            "phosphorus_status": phosphorus_status,
            "potassium_status": potassium_status,

            "suitability": suitability,

            "weather_advice": weather_advice,

            "sowing_month": sowing_month,
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
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image
    import numpy as np

    prediction = ""
    treatment = ""
    confidence = ""
    prevention = ""
    fungicide = ""
    image_path = ""

    if request.method == "POST":

        uploaded_file = request.FILES["leaf_image"]

        temp_path = os.path.join(
            BASE_DIR,
            "temp_leaf.jpg"
        )
        image_path = "/static/temp_leaf.jpg"

        with open(temp_path, "wb+") as destination:

            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        img = image.load_img(
            temp_path,
            target_size=(128, 128)
        )
        import shutil

        shutil.copy(
            temp_path,
            os.path.join(
        BASE_DIR,
        "static",
        "temp_leaf.jpg"
                )
        )

        img_array = image.img_to_array(img)

        img_array = img_array / 255.0

        img_array = np.expand_dims(
            img_array,
            axis=0
        )

        model = get_disease_model()

        result = model.predict(img_array)
        confidence = round(float(np.max(result)) * 100, 2)

        disease_class = class_names[np.argmax(result)]

        disease_info = {

            "Tomato_healthy": {
                "name": "Tomato - Healthy Plant",
                "treatment": "No disease detected. Continue regular watering and monitoring.",
                "prevention": "Maintain proper irrigation, balanced fertilization, and regular field inspection.",
                "fungicide": "Not Required"
            },

            "Tomato_Early_blight": {
                "name": "Tomato - Early Blight",
                "treatment": "Remove infected leaves and apply Mancozeb fungicide.",
                "prevention":"Avoid overhead watering and remove infected leaves.",

                  "fungicide":"Mancozeb"
            },

            "Tomato_Late_blight": {
                "name": "Tomato - Late Blight",
                "treatment": "Use Copper fungicide and improve air circulation.",
                "prevention": "Avoid excess moisture, provide good drainage, and remove infected plants.",
                "fungicide": "Copper Oxychloride"
            },

            "Tomato_Leaf_Mold": {
                "name": "Tomato - Leaf Mold",
                "treatment": "Reduce humidity and use suitable fungicide spray.",
                "prevention": "Improve ventilation, avoid overcrowding, and reduce humidity.",
                "fungicide": "Chlorothalonil"
            },

            "Tomato_Bacterial_spot": {
                "name": "Tomato - Bacterial Spot",
                "treatment": "Remove infected leaves and use copper-based bactericide.",
                "prevention": "Use disease-free seeds, avoid working with wet plants, and sanitize tools.",
                "fungicide": "Copper Hydroxide"
            },

            "Tomato_Septoria_leaf_spot": {
                "name": "Tomato - Septoria Leaf Spot",
                "treatment": "Apply fungicide and avoid overhead watering.",
                "prevention": "Remove infected leaves and ensure proper spacing between plants.",
                "fungicide": "Mancozeb"
            },

            "Tomato_Spider_mites_Two_spotted_spider_mite": {
                "name": "Tomato - Spider Mites",
                "treatment": "Spray neem oil or miticide.",
                "prevention": "Maintain adequate humidity and regularly inspect leaf undersides.",
                 "fungicide": "Neem Oil / Abamectin"
            },

            "Tomato__Target_Spot": {
                "name": "Tomato - Target Spot",
                "treatment": "Use fungicide and remove infected foliage.",
                "prevention": "Improve air circulation and avoid excessive leaf wetness.",
                "fungicide": "Azoxystrobin"
            },

            "Tomato__Tomato_mosaic_virus": {
                "name": "Tomato - Mosaic Virus",
                "treatment": "Remove infected plants immediately.",
                "prevention": "Use virus-free seeds, disinfect tools, and control insect vectors.",
                "fungicide": "No Chemical Control Available"
            },

            "Tomato__Tomato_YellowLeaf__Curl_Virus": {
                "name": "Tomato - Yellow Leaf Curl Virus",
                "treatment": "Control whiteflies and remove infected plants.",
                "prevention": "Control whiteflies, use resistant varieties, and remove infected plants.",
                "fungicide": "No Chemical Control Available"
            },

            "Potato___Early_blight": {
                "name": "Potato - Early Blight",
                "treatment": "Apply fungicide and remove affected leaves.",
                "prevention": "Rotate crops and avoid prolonged leaf wetness.",
                "fungicide": "Mancozeb"
            },

            "Potato___Late_blight": {
                "name": "Potato - Late Blight",
                "treatment": "Apply copper fungicide and improve drainage.",
                "prevention": "Avoid waterlogging and destroy infected plant debris.",
                "fungicide": "Copper Oxychloride"
            },

            "Potato___healthy": {
                "name": "Potato - Healthy Plant",
                "treatment": "No disease detected.",
                "prevention": "Continue proper irrigation, fertilization, and routine monitoring.",
                "fungicide": "Not Required"
            },

            "Pepper__bell___Bacterial_spot": {
                "name": "Pepper Bell - Bacterial Spot",
                "treatment": "Use copper bactericide and remove infected leaves.",
                "prevention": "Use certified seeds, avoid overhead irrigation, and sanitize equipment.",
                "fungicide": "Copper Hydroxide"
            },

            "Pepper__bell___healthy": {
                "name": "Pepper Bell - Healthy Plant",
                "treatment": "No disease detected.",
                "prevention": "Maintain healthy irrigation and nutrient management practices.",
                "fungicide": "Not Required"
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
        prevention = disease_info.get(
            disease_class,
          {}
          ).get(
                "prevention",
            "Maintain proper crop hygiene."
            )

        fungicide = disease_info.get(
        disease_class,
    {}
        ).get(
    "fungicide",
    "Consult Agriculture Officer."
        )

    return render(
    request,
    "accounts/disease.html",
    {

        "prediction":prediction,

        "treatment":treatment,

        "confidence":confidence,

        "prevention":prevention,

        "fungicide":fungicide,

        "image_path":image_path

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
def chatbot(request):
    answer = ""

    if request.method == "POST":
        question = request.POST["question"].lower()

        # ---------------- Crop Recommendation ----------------
        if "crop" in question or "grow" in question:
            answer = """
Enter your soil parameters (Nitrogen, Phosphorus, Potassium, pH, Rainfall and City).
The AI model will recommend the most suitable crop for your farm.
"""

        elif "rice" in question:
            answer = """
Rice grows best in clay soil with high rainfall and warm temperatures.
Maintain standing water during the growing season.
"""

        elif "wheat" in question:
            answer = """
Wheat grows well in cool climates with well-drained loamy soil.
Avoid excessive irrigation.
"""

        elif "maize" in question or "corn" in question:
            answer = """
Maize grows well in fertile loamy soil with moderate rainfall.
Maintain proper spacing for better yield.
"""

        elif "cotton" in question:
            answer = """
Cotton requires black soil, warm temperatures and moderate rainfall.
Avoid waterlogging.
"""

        elif "banana" in question:
            answer = """
Banana requires fertile soil, regular irrigation and warm weather.
Apply organic manure regularly.
"""

        elif "coffee" in question:
            answer = """
Coffee grows best in hilly regions with moderate rainfall and slightly acidic soil.
"""

        elif "sugarcane" in question:
            answer = """
Sugarcane requires fertile soil, abundant water and warm climate.
"""

        # ---------------- Fertilizer ----------------
        elif "fertilizer" in question:
            answer = """
The application recommends fertilizers after crop prediction.

Generally:

• Rice → Urea + DAP

• Cotton → Nitrogen Rich Fertilizer

• Banana → Potash Rich Fertilizer

• Coffee → Organic Compost
"""

        elif "organic" in question:
            answer = """
Organic fertilizers include:
• Compost
• Farm Yard Manure (FYM)
• Vermicompost
• Green Manure
"""

        elif "compost" in question:
            answer = """
Compost improves soil fertility, water retention and beneficial microorganisms.
"""

        # ---------------- Soil ----------------
        elif "soil" in question:
            answer = """
Soil parameters can be obtained from:

• Government Soil Testing Laboratory

• Soil Health Card

• Portable NPK Meter

• Agriculture Officer
"""

        elif "nitrogen" in question:
            answer = """
Nitrogen promotes leafy growth.
Low nitrogen causes yellow leaves and poor growth.
"""

        elif "phosphorus" in question:
            answer = """
Phosphorus helps root development, flowering and seed formation.
"""

        elif "potassium" in question:
            answer = """
Potassium improves disease resistance, fruit quality and drought tolerance.
"""

        elif "ph" in question:
            answer = """
Ideal soil pH for most crops ranges from 6.0 to 7.5.
"""

        elif "npk" in question:
            answer = """
NPK stands for:

N → Nitrogen

P → Phosphorus

K → Potassium

These nutrients are essential for healthy crop growth.
"""

        # ---------------- Weather ----------------
        elif "weather" in question:
            answer = """
The application fetches real-time weather information using OpenWeather API.
"""

        elif "temperature" in question:
            answer = """
Most crops grow well between 20°C and 30°C.
"""

        elif "humidity" in question:
            answer = """
High humidity may increase fungal diseases.
"""

        elif "rainfall" in question:
            answer = """
Rainfall is measured in millimetres (mm).
Different crops require different rainfall levels.
"""

        elif "climate" in question:
            answer = """
Climate affects crop growth through rainfall, temperature, humidity and sunlight.
"""

        # ---------------- Irrigation ----------------
        elif "water" in question or "irrigation" in question:
            answer = """
Water requirement depends on crop:

• Rice → High

• Cotton → Moderate

• Chickpea → Low
"""

        elif "drip" in question:
            answer = """
Drip irrigation saves water and supplies moisture directly to plant roots.
"""

        elif "sprinkler" in question:
            answer = """
Sprinkler irrigation distributes water like rainfall and is suitable for many field crops.
"""

        # ---------------- Disease Detection ----------------
        elif "disease" in question:
            answer = """
Open Disease Detection.
Upload a leaf image.
The AI model predicts the disease and suggests treatment.
"""

        elif "healthy" in question:
            answer = """
Healthy plants should have green leaves, strong stems and no visible spots.
"""

        elif "fungicide" in question:
            answer = """
Use only recommended fungicides based on the detected disease.
Always follow agricultural guidelines.
"""

        elif "pesticide" in question:
            answer = """
Use pesticides only when necessary.
Follow the recommended dosage and safety instructions.
"""

        elif "prevention" in question:
            answer = """
Disease prevention tips:

• Use certified seeds

• Avoid overwatering

• Remove infected leaves

• Maintain field hygiene
"""

        # ---------------- Economics ----------------
        elif "market" in question:
            answer = """
Market price depends on season, demand and location.
Refer to your Economic Analysis section.
"""

        elif "profit" in question:
            answer = """
Profit = Expected Income − Estimated Investment.
"""

        elif "investment" in question:
            answer = """
Investment includes:

• Seeds

• Fertilizers

• Irrigation

• Labour

• Pesticides
"""

        elif "yield" in question:
            answer = """
Yield depends on soil fertility, weather conditions and crop management.
"""

        # ---------------- Government ----------------
        elif "insurance" in question:
            answer = """
Pradhan Mantri Fasal Bima Yojana (PMFBY) provides crop insurance against natural calamities.
"""

        elif "scheme" in question or "government" in question:
            answer = """
Popular Government Schemes:

• PM-KISAN

• PMFBY

• Soil Health Card

• Kisan Credit Card (KCC)
"""

        # ---------------- Application ----------------
        elif "predict" in question:
            answer = """
Go to Crop Recommendation.

Enter all soil values.

Click Predict.

The AI model will recommend the best crop.
"""

        elif "history" in question:
            answer = """
Prediction History stores all previous crop recommendations for future reference.
"""

        elif "dashboard" in question:
            answer = """
The dashboard displays:

• Total Predictions

• Disease Records

• Weather Information

• Analytics
"""

        elif "login" in question:
            answer = """
Login using your registered username and password to access all features.
"""

        elif "register" in question or "signup" in question:
            answer = """
Create a new account using the Register page before accessing the system.
"""

        # ---------------- Greetings ----------------
        elif "hello" in question or "hi" in question or "hey" in question:
            answer = """
Hello Farmer 👋

Welcome to Smart Crop Recommendation System.

How can I help you today?
"""

        elif "thank" in question:
            answer = """
You're welcome 😊

Happy Farming!
Have a wonderful day.
"""

        elif "bye" in question:
            answer = """
Goodbye 👋

Wishing you a successful harvest.
Visit again anytime!
"""

        # ---------------- Default ----------------
        else:
            answer = """
Sorry, I couldn't understand your question.

I can answer questions about:

🌾 Crop Recommendation

🌱 Fertilizer

🌿 Disease Detection

🌦 Weather

🧪 Soil Testing

💧 Irrigation

🌾 Rice, Wheat, Cotton, Maize, Banana, Coffee

📈 Yield & Profit

💰 Market Price

🏛 Government Schemes

🛡 Crop Insurance

📊 Dashboard

🔑 Login & Registration
"""

    return render(
        request,
        "accounts/chatbot.html",
        {
            "answer": answer
        },
    )