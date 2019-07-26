import argparse
import asyncio
import logging
import os
import random

import cv2
from av import VideoFrame

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import ApprtcSignaling, TcpSocketSignaling

ROOT = os.path.dirname(__file__)
TMP_VIDEOS_PATH = os.path.join(ROOT, "temp", "videos")
PHOTO_PATH = os.path.join(ROOT, "temp", "images", "test.jpg")
IS_DEBUG = False


class FERtcSignaling(ApprtcSignaling):
    pass


class VideoImageTrack(VideoStreamTrack):
    """
    A video stream track that returns a rotating image.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.img = cv2.imread(PHOTO_PATH, cv2.IMREAD_COLOR)

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        # rotate image
        rows, cols, _ = self.img.shape
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), int(pts * time_base * 45), 1)
        img = cv2.warpAffine(self.img, M, (cols, rows))

        # create video frame
        frame = VideoFrame.from_ndarray(img, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base

        return frame


async def run(pc, player, recorder, signaling):
    def add_tracks():
        if player and player.audio:
            pc.addTrack(player.audio)

        if player and player.video:
            pc.addTrack(player.video)
        else:
            pc.addTrack(VideoImageTrack())

    @pc.on("track")
    def on_track(track):
        print("Track %s received" % track.kind)
        recorder.addTrack(track)

    # connect to websocket and join
    params = await signaling.connect()

    if params["is_initiator"] == "true":
        # send offer
        add_tracks()
        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()

            if obj.type == "offer":
                # send answer
                add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            pc.addIceCandidate(obj)
        elif obj is None:
            print("Exiting")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AppRTC")
    # parser.add_argument("room", nargs="?")
    parser.add_argument("--play-from", help="Read the media from a file and sent it."),
    # parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    # if not args.room:
        # args.room = "".join([random.choice("0123456789") for x in range(10)])

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection

    room_id: str = "".join([random.choice("0123456789") for x in range(10)])
    # signaling = ApprtcSignaling(args.room)
    signaling = FERtcSignaling(room_id)
    pc = RTCPeerConnection()

    # create media source
    if args.play_from:
        player = MediaPlayer(args.play_from)
    else:
        player = None

    unique_video_name = "".join([random.choice("0123456789") for x in range(10)]) + ".mp4"
    recorder = MediaRecorder(os.path.join(TMP_VIDEOS_PATH, unique_video_name))

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(pc=pc, player=player, recorder=recorder, signaling=signaling)
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
