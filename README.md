# YatriGPT
Yatri GPT is a travel information system that utilizes speech recognition and natural language processing to provide users with details about flights, restaurants, hotels, and nearby locations.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
  - [Clone the Repository](#clone-the-repository)
  - [Install Dependencies](#install-dependencies)
  - [Set up Environment Variables](#set-up-environment-variables)
  - [Run the Application](#run-the-application)
  - [Access the Application](#access-the-application)
- [Folder Structure](#folder-structure)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [License](#license)

## Features

- **Speech-to-Text Conversion:** Utilizes the SpeechRecognition library to convert spoken language into text.

- **Text-to-Speech Response:** Implements text-to-speech functionality using the pyttsx3 library to provide audio responses.

- **Intent Recognition and Processing:** Recognizes user intents from the spoken queries and processes them accordingly.

- **Flight Information Retrieval:** Fetches flight details using the TripAdvisor API, including source, destination, date, and pricing.

- **Restaurant Information Retrieval:** Retrieves restaurant information based on the specified city using the TripAdvisor API.

- **Hotel Information Retrieval:** Fetches hotel details based on location, check-in, and check-out dates from the TripAdvisor API.

- **Nearby Location Information:** Provides information about nearby locations, such as beaches, using external APIs.

# Getting Started

## Clone the Repository:

```bash
git clone https://github.com/your_username/Yatri-GPT.git
cd Yatri-GPT

## Install Dependencies:

```bash
pip install -r requirements.txt

# Set up Environment Variables:

- Replace 'your_trip_advisor_api_key_here' with your actual TripAdvisor API key.
- Define latitude_n and longitude_n.

# Run the Application:

```bash
python app.py






