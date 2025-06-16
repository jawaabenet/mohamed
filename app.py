import os
import uuid
from flask import Flask, request, jsonify, send_file
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import TextClip
from moviepy.video import fx

UPLOAD_DIR = 'uploads'
PROCESSED_DIR = 'processed'

app = Flask(__name__)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Utilities

def save_upload(file_storage, upload_dir=UPLOAD_DIR):
    video_id = str(uuid.uuid4())
    filename = os.path.join(upload_dir, f"{video_id}.mp4")
    file_storage.save(filename)
    return filename, video_id


def apply_filters(clip):
    # Example filter: simple colorx to brighten video
    return clip.fx(fx.MultiplyColor, 1.1)


def add_watermark(clip, text="Demo", pos=("right","bottom")):
    txt_clip = TextClip(text, fontsize=24, color='white', stroke_color='black', stroke_width=2)
    txt_clip = txt_clip.set_pos(pos).set_duration(clip.duration)
    return CompositeVideoClip([clip, txt_clip])


@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video part'}), 400
    file = request.files['video']
    filepath, video_id = save_upload(file)
    return jsonify({'video_id': video_id})


@app.route('/process/<video_id>', methods=['POST'])
def process(video_id):
    filepath = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
    if not os.path.exists(filepath):
        return jsonify({'error': 'Video not found'}), 404

    clip = VideoFileClip(filepath)
    clip = apply_filters(clip)

    if request.json.get('watermark'):
        clip = add_watermark(clip, text=request.json.get('watermark'))

    output_path = os.path.join(PROCESSED_DIR, f"{video_id}.mp4")
    clip.write_videofile(output_path, codec='libx264')
    clip.close()
    return jsonify({'processed_video_id': video_id})


@app.route('/download/<video_id>')
def download(video_id):
    output_path = os.path.join(PROCESSED_DIR, f"{video_id}.mp4")
    if not os.path.exists(output_path):
        return jsonify({'error': 'Processed video not found'}), 404
    return send_file(output_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
