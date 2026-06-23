import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import pickle

# Dataset Path
DATASET_PATH = r"C:\Users\91821\Desktop\SmartCropRecommendationSystem\Backend\PlantVillage"
# Image Settings
IMG_SIZE = (128, 128)
BATCH_SIZE = 32

# Data Generator
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    validation_split=0.2
)

train_generator = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="training"
)

validation_generator = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="validation"
)

# Save Class Names
class_names = list(train_generator.class_indices.keys())

with open("class_names.pkl", "wb") as f:
    pickle.dump(class_names, f)

# CNN Model
model = models.Sequential([

    layers.Conv2D(
        32,
        (3, 3),
        activation="relu",
        input_shape=(128, 128, 3)
    ),

    layers.MaxPooling2D(2, 2),

    layers.Conv2D(
        64,
        (3, 3),
        activation="relu"
    ),

    layers.MaxPooling2D(2, 2),

    layers.Conv2D(
        128,
        (3, 3),
        activation="relu"
    ),

    layers.MaxPooling2D(2, 2),

    layers.Flatten(),

    layers.Dense(
        256,
        activation="relu"
    ),

    layers.Dropout(0.3),

    layers.Dense(
        len(class_names),
        activation="softmax"
    )
])

# Compile
model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# Summary
model.summary()

# Train
history = model.fit(
    train_generator,
    validation_data=validation_generator,
    epochs=5
)

# Save Model
model.save("disease_model.keras")

print("\nTraining Complete")
print("Model Saved : disease_model.keras")
print("Classes Saved : class_names.pkl")