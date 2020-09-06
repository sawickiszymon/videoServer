import asyncio
import hashlib
import os
import time

import cv2
import imutils
import numpy as np
import ffmpeg
import json
from configparser import SafeConfigParser


from serverModule.log import log

config = SafeConfigParser()

config.read('config.ini')

opencv_width = config.getint('opencvVideoRes', 'width') # width
opencv_height = config.getint('opencvVideoRes', 'height') # height
encodingToCompressionRatio = config.get('ffmpeg', 'encodingSpeed')
resize_image = config.getboolean('opencvVideoRes', 'resize')


class CameraStream:
    FFMPEG_TIMEOUT = 60
    ffmpeg_process = None

    def __init__(self, uri, options=None):
        self.uri = uri
        self.key = self.get_key(uri)
        self.ws_list = list()

        self.options = options
        self.manage = options and options.get('should_end') or 0
        self.height = options and options.get('height') or 480
        self.width = options and options.get('width') or 640

    @staticmethod
    def get_key(uri):
        return hashlib.sha256(uri.encode('utf-8')).hexdigest()

    def ws_add(self, ws):
        self.ws_list.append(ws)

    def get_ws_list(self):
        return self.ws_list

    def ws_remove(self, ws):
        self.ws_list.remove(ws)

    async def ws_send(self, ws, frame):
        try:
            log.info(f'Send {self.key}: {len(frame)}')
            await ws.send_bytes(frame)
            await ws.drain()

            if ws._req.transport.is_closing():
                await ws.close()
        except Exception as error:
            await ws.close()

    async def start(self):
        width, height = await self.start_process()
        read_timeout, static_frame_change_time = 0, 0
        nextFrame, firstFrame = None, None
        ffmpeg_analysis_done = False

        try:
            while True:
                ret, image = self.cap.read()
                if ret:
                    # resize image - less computing power
                    # if resize_image:
                    image = cv2.resize(image, (width, height))

                    image, firstFrame, nextFrame, time_static_frame_change = \
                        self.detect_movement(image, firstFrame, nextFrame, static_frame_change_time)

                    # send 2 frames, so ffmpeg can finish input stream analysis
                    if not ffmpeg_analysis_done:
                        self.ffmpeg_process.stdin.writelines(image)
                        ffmpeg_analysis_done = True

                    self.ffmpeg_process.stdin.writelines(image)
                    await self.ffmpeg_process.stdin.drain()

                frame = await self._read_ffmpeg_stream()
                if frame:
                    read_timeout = 0
                    for ws in self.ws_list:
                        await self.ws_send(ws, frame)
                else:
                    read_timeout += 1
                    if read_timeout > self.FFMPEG_TIMEOUT:
                        return
        finally:
            await self.stop()

    async def stop(self):
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process = None
                self.cap.release()
                self.cap = None
            except ProcessLookupError:
                pass
            await asyncio.sleep(0.5)
        for ws in self.ws_list:
            await ws.close()

    def is_started(self):
        return self.ffmpeg_process is not None

    async def start_process(self):
        self.cap = cv2.VideoCapture(self.uri)
        if resize_image:  # resize image
            width = opencv_width
            height = opencv_height
        else:  # get VideoCapture width and height respectively
            width = int(self.cap.get(3))
            height = int(self.cap.get(4))

        args = (
            ffmpeg
                .input('-', pix_fmt='bgr24', format='rawvideo', framerate=20
                       , flags='low_delay', fflags='nobuffer'
                       , s='{}x{}'.format(width, height))
                .filter('scale', self.width, self.height)
                .output('pipe:1', format='h264',vprofile='baseline', pix_fmt='yuv420p',
                        tune='zerolatency',preset=encodingToCompressionRatio)
                .get_args()
        )

        self.ffmpeg_process = await asyncio.create_subprocess_exec('ffmpeg', *args, stdout=asyncio.subprocess.PIPE,
                                                                   stdin=asyncio.subprocess.PIPE)
        return width, height


    def get_json_object(self):
        return dict(
            uri=self.uri,
            key=self.key,
            options=self.options,
            ws=f'/ws/{self.key}'
        )

    def detect_movement(self, image, first_frame, next_frame, time_change_static):
        # convert it to grayscale, and blur it
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # if the first frame is None, initialize it
        if first_frame is None:
            first_frame = gray

        time_change_static += 1
        # Update first frame
        if time_change_static > 20:
            delay = 0
            first_frame = next_frame

        next_frame = gray

        frameDelta = cv2.absdiff(first_frame, next_frame)
        thresh = cv2.threshold(frameDelta, 30, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # find contours on thresholded image
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        for c in cnts:
            # if the contour is big enough, draw the rectangle
            if cv2.contourArea(c) > 30000:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return image, first_frame, next_frame, time_change_static

    async def read_ffmpeg_stream(self):
        if self.ffmpeg_process:
            in_bytes = await self.ffmpeg_process.stdout.read(2048 * 1024)
            if in_bytes is None:
                return None
            return in_bytes
        else:
            return None


class StreamPool:
    streams = dict()

    async def get_streams(self):
        return self.streams


    async def create_stream(self, uri, options):
        key = CameraStream.get_key(uri)
        if key not in self.streams:
            self.streams[key] = CameraStream(uri, options)
            loop = asyncio.get_event_loop()
            loop.create_task(self.streams[key].start())
        return self.streams[key]

    async def delete_stream(self, uri):
        key = CameraStream.get_key(uri)
        if key in self.streams:
            loop = asyncio.get_event_loop()
            loop.create_task(self.streams[key].stop())
            del self.streams[key]