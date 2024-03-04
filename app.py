import datetime
import os
import subprocess
from flask import Flask, jsonify, request, Response, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import whisper
import uuid
import tempfile
import glob
from threading import Thread
import threading
import time
from flask_socketio import SocketIO
import base64
import asyncio


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


# Add this decorator to apply the header to all responses
@app.after_request
def add_security_headers(response):
    # Set the Content Security Policy to allow loading from any source
    response.headers["Content-Security-Policy"] = "default-src 'self' *;"

    return response


def convert_blob_to_wav(blob):
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, str(uuid.uuid4()) + ".wav")

    with open(temp_path, "wb") as wav_file:
        wav_file.write(blob)

    print(f"Saved file at: {temp_path}")
    return temp_path


def send_transcription(result):
    socketio.emit("transcription_update", {"transcription": result})


def transcribe_audio(chunk_path, file_name):
    socketio.start_background_task(
        target=send_hello_world, message="in the transcripting"
    )

    model = whisper.load_model("base")
    print(chunk_path)
    audio_path = os.path.abspath(chunk_path)

    try:
        result = model.transcribe(audio_path)
        print(result)
        socketio.start_background_task(target=send_transcription, result=result)

    except Exception as e:
        print(f"Error during transcription: {e}")
    finally:
        os.remove(chunk_path)


@app.route("/")
def index():
    return render_template("index.html")


# async def send_message(key , message):
#     await asyncio.sleep(1)  # Simulating an async operation
#     socketio.emit(key, message)


def send_message(key, message):
    print("int he message")

    socketio.send({"key": key, "message": message})
    socketio.sleep(1)

@socketio.on("connect")
def handle_connect():
    # message = "mesage is this"
    print("Client connected")
    # socketio.start_background_task(target=send_message, key = "message", message = message)


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


def timestamp_to_seconds(timestamp):
    print("timestamp", timestamp)
    time_obj = datetime.datetime.strptime(str(timestamp), "%H:%M:%S")
    total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    return total_seconds


def convert_time_format(time_str, output_format="%H:%M:%S"):
    # Determine if the time is positive or negative
    is_negative = False
    if time_str.startswith("-"):
        is_negative = True
        time_str = time_str[1:]
    elif time_str.startswith("+"):
        time_str = time_str[1:]

    # Convert the time string to a timedelta object
    time_delta = datetime.datetime.strptime(time_str, "%H:%M:%S").time()

    # Adjust the timedelta object for negative time
    
        # time_delta = datetime.timedelta(
        #     hours=time_delta.hour,
        #     minutes=time_delta.minute,
        #     seconds=time_delta.second,
        # )
    
    time_delta = datetime.timedelta(
        hours=time_delta.hour, minutes=time_delta.minute, seconds=time_delta.second
    )

    # Format the timedelta object using the desired format
    formatted_time = (datetime.datetime.min + time_delta).time()

    return formatted_time.strftime(output_format)


# Function to convert seconds to HH:MM:SS format
def convert_seconds_to_timestamp(seconds):

    return str(datetime.timedelta(seconds=seconds))

    #     return jsonify({'error': 'Invalid file type'}), 400


# @socketio.on("start_transcription")
def start_transcription(
    file_name, time_stamps, audio_duration, duration, offset, timeStampsType
):

    # socketio.start_background_task(target=send_hello_world, message=message)

    # file_content_base64 = message.get("file")
    # # file = message.get("file")
    # file_name = message.get("fileName")
    # time_stamps = message.get("timeStamps")
    # audio_duration = message.get("audioDuration")
    # Decode base64 to get the file content
   
    # file_content = file_content_base64.encode("utf-8")
    file_name = file_name.replace(" ", "_")
    # Save the file to a temporary path
    temp_file_path = "./temps2/" + file_name

    # with open(temp_file_path, "wb") as temp_file:
    #     temp_file.write(file_content_base64)
    socketio.start_background_task(target=send_message, key="message", message="in the transcripting")
    # Do something with the temporary file...
    # print(f"File saved to {temp_file_path}")
    # total_duration = timestamp_to_seconds(audio_duration)
    # print(time_stamps)
    for key, timestamp in enumerate(time_stamps):

        formated_time = ""
        timetamp_sec = ""
        if not isinstance(timestamp, str) or ":" not in timestamp:
            try:
                timetamp_sec = float(timestamp) * 3600
            except ValueError:
                print("convertion failed: ", ValueError)
                continue
        else:
            formated_time = convert_time_format(timestamp)
            timetamp_sec = timestamp_to_seconds(formated_time)

        starting_timestamp_sec = timetamp_sec
        if timeStampsType == "end":
            starting_timestamp_sec = float(audio_duration) - timetamp_sec
        starting_timestamp = convert_seconds_to_timestamp(
            starting_timestamp_sec - float(offset)
        )

        print(starting_timestamp)
        chunk_path = f"./temps/{file_name}_trimmed_{str(key)}.wav"
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i",
            temp_file_path,
            "-ss",
            starting_timestamp,  # Start time in seconds
            "-t",
            duration,  # Duration in seconds
            "-c",
            "copy",
            chunk_path,
        ]

        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error during trimming: {result.stderr}")
            # Handle the error as needed

        # Start transcription for the specific chunk
        # transcription_thread = threading.Thread(
        #     target=transcribe_audio, args=(chunk_path, file_name)
        # )
        # transcription_thread.start()
        # transcription_thread.join()
        transcribe_audio(chunk_path, file_name)


@socketio.on("stop_transcription")
def stop_transcription():
    print("Stopping transcription")

@app.route("/is-audio-exists", methods=["POST"])
def is_audio_exists():
    file_name = request.form.get("fileName")
    file_name = file_name.replace(" ", "_")
    file_path = f"./temps2/{file_name}"
    print(file_path)
    if os.path.exists(file_path):
        return jsonify({"exists": True}), 200
    else:
        return jsonify({"exists": False}), 200

@app.route("/upload", methods=["POST"])
def upload():
    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)

        target_path = "./temps2"
        file_path = os.path.join(target_path, filename)

        # Check if a file with the same name already exists
        if os.path.exists(file_path):
            send_message("message","File already exists")
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join("./temps2", filename))
            send_message("message","File saved successfully")
    

    # return jsonify({"message": "file saved successfully"}), 200
    # Get other form fields
    file_name = request.form.get('fileName')
    time_stamps = request.form.get("timeStamps")
    audio_duration = request.form.get("audioDuration")
    duration = request.form.get("duration")
    offset = request.form.get("offset")
    timeStampsType = request.form.get("timeStampsType")
    captured_time = request.form.get("capturedTime")

    target_path = "./temps2"
    file_path = os.path.join(target_path, file_name)
    # message = "in the start transcription"
    # socketio.emit("message", message)
    # Process other form fields as needed
    print("File Name:", file_name)
    print("Time Stamps:", time_stamps)
    print("Audio Duration:", audio_duration)

    time_stamps_list = time_stamps.split(",")
    # start_transcription(
    #     file_name, time_stamps_list, audio_duration, duration, offset, timeStampsType
    # )

    # socketio.start_background_task(target=send_hello_world, message="in the upload")
    try:
        send_message("message","in the start transcripting")
    except RuntimeError:
        pass
    finally:
        print('in the final')
        pass
    # socketio.send(message)
    print('outside the final')

    # file_content = file_content_base64.encode("utf-8")
    file_name = file_name.replace(" ", "_")
    # Save the file to a temporary path
    temp_file_path = "./temps2/" + file_name

    # with open(temp_file_path, "wb") as temp_file:
    #     temp_file.write(file_content_base64)

    # Do something with the temporary file...
    # print(f"File saved to {temp_file_path}")
    # total_duration = timestamp_to_seconds(audio_duration)
    # print(time_stamps)
    for key, timestamp in enumerate(time_stamps_list):

        formated_time = ""
        timetamp_sec = ""
        starting_timestamp = 0
        print(timeStampsType)
        if(captured_time == "false"):
            if not isinstance(timestamp, str) or ":" not in timestamp:
                try:
                    print("timestamp", timestamp)
                    timetamp_sec = float(timestamp) * 3600
                except ValueError:
                    print("convertion failed: ", ValueError)
                    continue
            else:
                formated_time = convert_time_format(timestamp)
                timetamp_sec = timestamp_to_seconds(formated_time)
            if (timeStampsType == "start"):
                starting_timestamp = timetamp_sec
            elif( timeStampsType == "end"):
                timetamp_sec = float(audio_duration) - timetamp_sec

            starting_timestamp = str(timetamp_sec - float(offset))

            # starting_timestamp = convert_seconds_to_timestamp(
            #     timetamp_sec - float(offset)
            # )
            print(starting_timestamp)
        else:
            starting_timestamp = timestamp
            pass
        print(captured_time , " " , timestamp, " ", starting_timestamp, " ", timeStampsType)
        # return jsonify({"message": "file saved successfully"}), 200
        print(starting_timestamp)
        chunk_path = f"./temps/{file_name}_trimmed_{str(uuid.uuid3(uuid.NAMESPACE_OID, str(key)))}.wav"
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i",
            temp_file_path,
            "-ss",
            starting_timestamp,  # Start time in seconds
            "-t",
            duration,  # Duration in seconds
            "-c",
            "copy",
            chunk_path,
        ]

        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error during trimming: {result.stderr}")
            # Handle the error as needed

        send_message("message", "in the transcripting")

        model = whisper.load_model("base")
        print(chunk_path)
        audio_path = os.path.abspath(chunk_path)

        try:
            result = model.transcribe(audio_path)
            print(result)
            send_message("result",result)
            socketio.start_background_task(target=send_transcription, result=result)

        except Exception as e:
            print(f"Error during transcription: {e}")
        finally:
            os.remove(chunk_path)

    return jsonify({"message": "File uploaded successfully"}), 200  


@app.route("/transcribe", methods=["POST"])
def transcribe_audio_api():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    audio_blob = request.files["file"].read()

    # Convert blob to WAV using ffmpeg
    wav_file_path = convert_blob_to_wav(audio_blob)

    # Transcribe using Whisper ASR model
    model = whisper.load_model("base")
    audio_path = os.path.abspath(wav_file_path)
    result = model.transcribe(audio_path)
    os.remove(wav_file_path)
    return jsonify(result)


def run_socketio():
    print("Initializing SocketIO server...")
    app.run(host="0.0.0.0", port=5112, debug=True)


if __name__ == "__main__":
    # socketio_thread = threading.Thread(target=run_socketio)
    # socketio_thread.start()
    # print("Running Flask app with Gunicorn...")

    # socketio.run(app, host="0.0.0.0", port=5111, debug=True)

    socketio.run(app, host="0.0.0.0", port=5111, debug=True)
    # # Allow some time for the SocketIO server to start before running the main Flask app
    # time.sleep(2)
    

    # print("Running Flask app...")
    # app.run(host="0.0.0.0", port=5112)
    # eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5112)), app)
