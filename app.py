import datetime
import json
import os
from queue import Queue
import re
import psutil
import math
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
import requests

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# root_url = "http://localhost/noteclimberConnection.php"
root_url = "https://www.noteclimber.com/noteclimberConnection.php"


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


def scroll_update(result):
    socketio.emit("scroll_update", {"result": result})


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
    try:
        print("timestamp", timestamp)
        time_obj = datetime.datetime.strptime(str(timestamp), "%H:%M:%S")
        total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
        return total_seconds
    except ValueError:
        # Handle the case when the time string does not match the format
        return None


def extract_time_string(time_str):
    # Use regular expression to find time string
    match = re.search(r"(\d{1,2}:\d{1,2}:\d{1,2})", time_str)
    if match:
        return match.group(1)
    else:
        return None


def convert_time_format(time_str, output_format="%H:%M:%S"):
    # Extract the time string from input
    if "." in time_str:
        time_str = time_str.replace(".", ":")
    extracted_time_str = extract_time_string(time_str)
    if extracted_time_str:
        # Determine if the time is positive or negative
        is_negative = False
        if extracted_time_str.startswith("-"):
            is_negative = True
            extracted_time_str = extracted_time_str[1:]
        elif extracted_time_str.startswith("+"):
            extracted_time_str = extracted_time_str[1:]

        # Split the time string into its components
        time_parts = extracted_time_str.split(":")

        # Fill missing components with zeros
        while len(time_parts) < 3:
            time_parts.append("0")

        # Convert components to integers
        hours, minutes, seconds = map(int, time_parts)

        # Create a timedelta object
        time_delta = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

        # Format the timedelta object using the desired format
        formatted_time = (datetime.datetime.min + time_delta).time()

        return formatted_time.strftime(output_format)
    else:
        return None


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
    file_name = secure_filename(file_name)
    # Save the file to a temporary path
    temp_file_path = "./temps2/" + file_name

    # with open(temp_file_path, "wb") as temp_file:
    #     temp_file.write(file_content_base64)
    socketio.start_background_task(
        target=send_message, key="message", message="in the transcripting"
    )
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
    file_name = secure_filename(file_name)
    file_path = f"./temps2/{file_name}"
    print(file_path)
    if os.path.exists(file_path):
        return jsonify({"exists": True}), 200
    else:
        return jsonify({"exists": False}), 200


task_queue = Queue()


# Function to process the uploaded file and start transcription
def process_upload(
    file_name,
    time_stamps,
    audio_duration,
    duration,
    offset,
    time_stamps_type,
    captured_time,
    user_id,
    pdf_text,
    book_name,
    trans_id,
):
    target_path = "./temps2"
    if not os.path.exists(target_path):
        os.mkdir(target_path)
    file_path = os.path.join(target_path, file_name)

    file_name = secure_filename(file_name)
    # Process other form fields as needed
    print("File Name:", file_name)
    print("Time Stamps:", time_stamps)
    print("Audio Duration:", audio_duration)
    # Add file name in the db and retreive the id to use it in updataing row on each timestamp completeion of process

    time_stamps_list = time_stamps.split(",")
    transcriptions = []
    total_expected_timestamps = len(time_stamps_list)
    timestamps_computed = 0

    for key, timestamp in enumerate(time_stamps_list):
        formated_time = ""
        timetamp_sec = ""
        starting_timestamp = 0
        if captured_time == "false":
            if not isinstance(timestamp, str) or ":" not in timestamp:
                try:
                    timetamp_sec = float(timestamp) * 3600
                except ValueError:
                    continue
            else:
                formated_time = convert_time_format(timestamp)
                timetamp_sec = timestamp_to_seconds(formated_time)
            if time_stamps_type == "start":
                starting_timestamp = timetamp_sec
            elif time_stamps_type == "end":
                timetamp_sec = float(audio_duration) - timetamp_sec
            starting_timestamp = str(timetamp_sec - float(offset))
        else:
            starting_timestamp = timestamp
        if os.path.exists("./temps") == False:
            os.mkdir("./temps")
        chunk_path = f"./temps/{file_name}_trimmed_{str(uuid.uuid3(uuid.NAMESPACE_OID, str(key)))}.wav"
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i",
            os.path.join(target_path, file_name),
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
            transcriptions.append(result)
            send_message("result", result)

            timestamps_computed += 1
            percentage_completion = (
                timestamps_computed / total_expected_timestamps
            ) * 100

            api_url = root_url + "/api/update-trans"
            response = requests.post(
                api_url,
                data={
                    "trans_id": trans_id,
                    "new_trans": json.dumps([result]),
                    "status": percentage_completion,
                },
            )
            print(response.text)
            print(response.status_code)
            socketio.start_background_task(target=send_transcription, result=result)

        except Exception as e:
            print(f"Error during transcription: {e}")
        finally:
            os.remove(chunk_path)

    # Post process the transcriptions or perform any other operations
    print("File Name:", file_name)
    print("User ID:", user_id)
    print("PDF Text:", pdf_text)
    print("Book Name:", book_name)
    print("Transcriptions:", transcriptions)

    # Now, you can make the API call to store transcriptions


audio_book_queue = Queue()


# Function to handle the API upload endpoint
def upload():
    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)

        target_path = "./temps2"
        if os.path.exists(target_path) == False:
            os.mkdir(target_path)
        file_path = os.path.join(target_path, filename)

        # Check if a file with the same name already exists
        if os.path.exists(file_path):
            send_message("message", "File already exists")
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join("./temps2", filename))
            send_message("message", "File saved successfully")

    # Get other form fields
    file_name = request.form.get("fileName")
    time_stamps = request.form.get("timeStamps")
    audio_duration = request.form.get("audioDuration")
    duration = request.form.get("duration")
    offset = request.form.get("offset")
    time_stamps_type = request.form.get("timeStampsType")
    captured_time = request.form.get("capturedTime")
    user_id = request.form.get("userId")
    pdf_text = request.form.get("pdfText")
    book_name = request.form.get("bookName")

    api_url = root_url + "/api/store-trans"
    response = requests.post(
        api_url,
        data={
            "file_name": file_name,
            "time_stamps": time_stamps,
            "user_id": user_id,
            "pdfText": pdf_text,
            "bookName": book_name,
            "transcriptions": json.dumps([]),
        },
    )
    res = json.loads(response.text)

    trans_id = res["response"]["insert_id"]

    print(trans_id)
    api_url = root_url + "/api/check-stored-whole-trans"
    response = requests.post(
        api_url,
        data={
            "audio_book_name": file_name,
        },
    )
    if response.status_code == 200:
        res = json.loads(response.text)

        res_json = json.loads(res)

        result = process_if_found(
            res_json,
            time_stamps,
            audio_duration,
            duration,
            offset,
            time_stamps_type,
            captured_time,
        )
        socketio.start_background_task(target=send_transcription, result=result)

        return jsonify({"message": "processing Completed!"}), 200

    api_url = root_url + "/api/reserver-whole-trans"

    response = requests.post(
        api_url,
        data={
            "audio_book_name": file_name,
            "user_id": user_id,
            "status": "Queue",
            "time_stamps": time_stamps,
            "pdf_text": pdf_text,
            "book_name": book_name,
        },
    )
    
    res = json.loads(response.text)
    whole_book_id = res["insert_id"]
    print(whole_book_id)    
    # Enqueue the processing task
    if(len(time_stamps) != 0):
        task_queue.put(
            lambda: process_upload(
                file_name,
                time_stamps,
                audio_duration,
                duration,
                offset,
                time_stamps_type,
                captured_time,
                user_id,
                pdf_text,
                book_name,
                trans_id,
            )
        )
    audio_book_queue.put(
        lambda: transcribe_audio_book(file_name, audio_duration, user_id, pdf_text,
        book_name, whole_book_id)
    )
    return jsonify({"message": "File processing request queued!"}), 200


def process_if_found(
    transcription,
    time_stamps,
    audio_duration,
    duration,
    offset,
    time_stamps_type,
    captured_time,
):
    if transcription:
        time_stamps_list = time_stamps.split(",")
        transcriptions = []

        for timestamp in time_stamps_list:
            formatted_time = ""
            timestamp_sec = ""
            starting_timestamp = 0

            if captured_time == "false":
                if not isinstance(timestamp, str) or ":" not in timestamp:
                    try:
                        timestamp_sec = float(timestamp) * 3600
                    except ValueError:
                        continue
                else:
                    formatted_time = convert_time_format(timestamp)
                    timestamp_sec = timestamp_to_seconds(formatted_time)

                if time_stamps_type == "start":
                    starting_timestamp = timestamp_sec
                elif time_stamps_type == "end":
                    timestamp_sec = float(audio_duration) - timestamp_sec
                starting_timestamp = str(timestamp_sec - float(offset))
            else:
                starting_timestamp = timestamp

            # Find the segment containing the starting timestamp
            start_segment = None
            end_segments = []

            for seg in transcription["segments"]:
                if seg["start"] <= float(starting_timestamp) <= seg["end"]:
                    start_segment = seg
                    continue

                print(
                    # seg["start"]
                    # <= float(starting_timestamp) + float(duration)
                    seg["end"]
                )

                if (
                    float(starting_timestamp)
                    <= seg["start"]
                    <= float(starting_timestamp) + float(duration)
                    <= seg["end"]
                ):
                    end_segments.append(seg)
                    continue
                elif float(starting_timestamp) + float(duration) < seg["end"]:
                    break
                elif start_segment:
                    end_segments.append(seg)

            if start_segment:
                segs = []
                text = ""
                # Extract text from the start segment
                segs.append(start_segment)
                text += start_segment["text"]

                # Extract text from the end segments
                for segment in end_segments:
                    segs.append(segment)
                    text += segment["text"]

                transcriptions.append({"text": text, "segments": segs})

        return transcriptions[0]

    return None


# Route for handling upload endpoint
app.route("/upload", methods=["POST"])(upload)


def transcribe_audio_book(
    file_name, audio_duration, user_id, pdf_text, book_name, whole_book_id
):
    file_name = secure_filename(file_name)
    # Convert audio_duration to integer
    audio_duration = int(math.ceil(float(audio_duration)))  # Round float to nearest integer

    # Check if the file is already processed
    response = requests.post(
        root_url + "/api/check-stored-whole-trans", data={"audio_book_name": file_name}
    )
    if response.status_code == 200:
        return

    # Define segment duration (in seconds)
    segment_duration = 50
    insert_id = whole_book_id
    # reserver_response = requests.post(
    #     root_url + "/api/reserver-whole-trans", data={"audio_book_name": file_name, "pdf_text":pdf_text, "book_name":book_name, "user_id":user_id}
    # )
    # if reserver_response.status_code == 200:
    #     # Extract the insert ID from the response JSON
    #     response_data = reserver_response.json()
    #     insert_id = response_data.get('insert_id')
    # Create a directory for storing segments if it doesn't exist
    target_path = "./segments"
    if not os.path.exists(target_path):
        os.mkdir(target_path)

    # Replace spaces in file name with underscores
    new_file_name = file_name

    # Initialize list to store segment transcriptions
    all_segments = []

    # Initialize text for concatenation
    concatenated_text = ""
    print("file name is in whole trans: " + file_name)
    # Iterate through each segment
    # Set the target directory

    for segment_start in range(0, audio_duration, segment_duration):
        # Calculate segment end time
        segment_end = min(segment_start + segment_duration, audio_duration)

        # Generate output file path for the segment
        segment_file_path = os.path.join(
            target_path, f"{segment_start}-{segment_end}_{new_file_name}"
        )
        target_path = "temps2"

        # Construct input file path
        input_file_path = os.path.join(target_path, file_name)
        print(input_file_path)

        # Check if the input file exists
        if not os.path.exists(input_file_path):
            print("File does not exist. Skipping segment.")
            continue

        # Extract segment using ffmpeg
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i",
            input_file_path,
            "-ss",
            str(segment_start),  # Start time in seconds
            "-t",
            str(segment_end),  # Duration in seconds
            "-c",
            "copy",
            segment_file_path
        ]

        try:
            subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as ex:
            print(ex)
            print(input_file_path)
            return

        # Transcribe the segment
        model = whisper.load_model("base")
        try:
            result = model.transcribe(segment_file_path)
            status = calculate_status(segment_start, audio_duration)

            reserver_response = requests.post(
                root_url + "/api/update-status-whole-trans", data={"status": status, "row_id": insert_id}
            )
            print(reserver_response.text)
            # Update segment objects with segment_start value and concatenate text
            for segment in result["segments"]:
                segment["start"] += segment_start
                segment["end"] += segment_start
                concatenated_text = concatenated_text + segment["text"]
                all_segments.append(segment)

        except Exception as e:
            print(
                f"Error during transcription of segment {segment_start}-{segment_end}: {e}"
            )

        # Delete segment file to save space
        os.remove(segment_file_path)

    # Create final result object
    final_result = {
        "text": concatenated_text,
        "segments": all_segments,
        "language": "en",  # You may need to update this based on the language
    }

    # Store the final result in the database
    response = requests.post(
        root_url + "/api/store-whole-trans",
        data={
            "trans": json.dumps(final_result),
            "row_id": insert_id,
            "status": "100"
        },
    )
    if response.status_code == 200:
        print(response.text)

    print("Transcription completed.")


# Calculate status function
def calculate_status(segment_start, audio_duration):
    progress = (segment_start / audio_duration) * 100
    if progress < 50:
        return "In Progress"
    elif progress >= 50 and progress < 100:
        return "Almost Complete"
    else:
        return "Complete"
def start_audio_book_queue_processing():
    print("Starting audio book queue processing...")
    while True:
        task = audio_book_queue.get()
        print("Processing audio book...")
        task()
        audio_book_queue.task_done()    

# Function to limit CPU usage for a thread
def limit_cpu_usage(thread, limit):
    p = psutil.Process(thread.ident)
    p.cpu_affinity([0])  # Limit to the first CPU core
    p.nice(10) # for linux
    # p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)  # Lower the priority for windows

# Start the audio book queue processing thread
audio_worker = threading.Thread(target=start_audio_book_queue_processing)
audio_worker.daemon = True
# limit_cpu_usage(audio_worker, 0.5)  # Limit to 50% CPU usage
audio_worker.start()

# Function to start the background thread to process the queue
def start_queue_processing():
    print("start queue processing")
    while True:
        task = task_queue.get()
        print("processing...")
        task()
        task_queue.task_done()


# Start the background thread
worker = Thread(target=start_queue_processing)
worker.daemon = True
worker.start()

transcription_running = True


@app.route("/test-api", methods=["POST"])
def test_api():
    file_name = request.form.get("fileName")
    time_stamps = request.form.get("timestamps")
    user_id = request.form.get("userId")
    pdfText = request.form.get("pdfText")
    bookName = request.form.get("bookName")
    print(bookName)
    transcriptions = request.form.get("transcriptions")
    print(transcriptions)
    api_url = root_url + "/api/store-trans"
    print(api_url)
    response = requests.post(
        api_url,
        data={
            "file_name": file_name,
            "time_stamps": time_stamps,
            "user_id": user_id,
            "pdfText": pdfText,
            "bookName": bookName,
            "transcriptions": json.dumps(transcriptions),
        },
    )
    print(response.text)
    print(response.status_code)
    return jsonify({"message": "File uploaded successfully" + str(response)}), 200


@socketio.on("scroll-to-text")
def scroll_to_text(data):
    global transcription_running
    transcription_running = True

    current_time = data["current_time"]
    audio_duration = data["audio_duration"]
    file_name = data["file_name"]
    file_name = secure_filename(file_name)
    temp_file_path = "./temps2/" + file_name
    audio_length = 30
    current_time = float(current_time)
    audio_duration = float(audio_duration)
    while transcription_running:

        print(current_time)
        print(audio_duration)

        if os.path.exists("./temps") == False:
            os.mkdir("./temps")
        chunk_path = f"./temps/{file_name}_trimmed_{str(uuid.uuid3(uuid.NAMESPACE_OID, str(current_time)))}.wav"
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i",
            temp_file_path,
            "-ss",
            str(current_time),  # Start time in seconds
            "-t",
            str(audio_length),  # Duration in seconds
            "-c",
            "copy",
            chunk_path,
        ]

        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error during trimming: {result.stderr}")
            # Handle the error as needed

        model = whisper.load_model("base")
        print(chunk_path)
        audio_path = os.path.abspath(chunk_path)

        try:
            result = []
            print(current_time)
            result = model.transcribe(audio_path)
            print(result)
            result = {"result": result, "current_time": current_time}
            send_message("result", result)
            socketio.start_background_task(target=scroll_update, result=result)

        except Exception as e:
            print(f"Error during transcription: {e}")
        finally:
            os.remove(chunk_path)
        if current_time >= audio_duration:
            break
        else:
            current_time += audio_length


@app.route("/stop-scroll", methods=["POST"])
def stop_transcription():
    global transcription_running
    transcription_running = False
    return jsonify({"message": "Scroll process stopped"}), 200


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


@app.route("/store-audio", methods=["POST"])
def store_audio():
    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        print(file.filename)
        filename = secure_filename(file.filename)

        target_path = "./temps2"

        if os.path.exists(target_path) == False:
            os.mkdir(target_path)
        file_path = os.path.join(target_path, filename)

        # Check if a file with the same name already exists
        if os.path.exists(file_path):
            send_message("message", "File already exists")
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join("./temps2", filename))
            send_message("message", "File saved successfully")
            return jsonify({"message": "File saved successfully"}), 200


def run_socketio():
    print("Initializing SocketIO server...")
    app.run(host="0.0.0.0", port=5112, debug=True)


if __name__ == "__main__":
    # socketio_thread = threading.Thread(target=run_socketio)
    # socketio_thread.start()
    # print("Running Flask app with Gunicorn...")

    # socketio.run(app, host="0.0.0.0", port=5111, debug=True)

    # socketio.run(app, host="0.0.0.0", port=5111, debug=True)
    socketio.run(app, host="0.0.0.0", port=5111, allow_unsafe_werkzeug=True)
    # # Allow some time for the SocketIO server to start before running the main Flask app
    # time.sleep(2)

    # print("Running Flask app...")
    # app.run(host="0.0.0.0", port=5112)
    # eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5112)), app)
