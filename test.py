def process_if_found(
    transcription,
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


# Example usage:
transcription = {
    "text": "By the evening in New York in the early spring of 2006, I'm in my combined 60 minutes and 60 minutes to office at 555 West 57th across the street.",
    "segments": [
        {
            "id": 0,
            "seek": 0,
            "start": 0.0,
            "end": 11.0,
            "text": "By the evening in New York in the early spring of 2006, I'm in my combined 60 minutes and 60 minutes to office at 555 West 57th across the street.",
            "tokens": [
                50364,
                3146,
                264,
                5634,
                294,
                1873,
                3609,
                294,
                264,
                2440,
                5587,
                295,
                14062,
                11,
                286,
                478,
                294,
                452,
                9354,
                4060,
                2077,
                293,
                4060,
                2077,
                281,
                3398,
                412,
                12330,
                20,
                4055,
                21423,
                392,
                2108,
                264,
                4838,
                13,
                50914,
            ],
            "temperature": 0.0,
            "avg_logprob": -0.3113137546338533,
            "compression_ratio": 1.226890756302521,
            "no_speech_prob": 0.125856414437294,
        },
        {
            "id": 0,
            "seek": 0,
            "start": 18.0,
            "end": 20.0,
            "text": "testing another one",
            "tokens": [
                50364,
                3146,
                264,
                5634,
                294,
                1873,
                3609,
                294,
                264,
                2440,
                5587,
                295,
                14062,
                11,
                286,
                478,
                294,
                452,
                9354,
                4060,
                2077,
                293,
                4060,
                2077,
                281,
                3398,
                412,
                12330,
                20,
                4055,
                21423,
                392,
                2108,
                264,
                4838,
                13,
                50914,
            ],
            "temperature": 0.0,
            "avg_logprob": -0.3113137546338533,
            "compression_ratio": 1.226890756302521,
            "no_speech_prob": 0.125856414437294,
        },
        {
            "id": 0,
            "seek": 0,
            "start": 30.0,
            "end": 40.0,
            "text": "testing another one",
            "tokens": [
                50364,
                3146,
                264,
                5634,
                294,
                1873,
                3609,
                294,
                264,
                2440,
                5587,
                295,
                14062,
                11,
                286,
                478,
                294,
                452,
                9354,
                4060,
                2077,
                293,
                4060,
                2077,
                281,
                3398,
                412,
                12330,
                20,
                4055,
                21423,
                392,
                2108,
                264,
                4838,
                13,
                50914,
            ],
            "temperature": 0.0,
            "avg_logprob": -0.3113137546338533,
            "compression_ratio": 1.226890756302521,
            "no_speech_prob": 0.125856414437294,
        },
    ],
    "language": "en",
}

time_stamps = "0.0"
audio_duration = "3600"
duration = "30"
offset = "0"
time_stamps_type = "start"
captured_time = "false"
user_id = "12345"
pdf_text = ""
book_name = "MyBook"
trans_id = "1"

result = process_if_found(
    transcription,
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
print(result)
