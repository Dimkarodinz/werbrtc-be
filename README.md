# Description
Example WEBRTC server application.
Simulate one peer, save incoming flow into temp video file, sends it to S3.

This application counl be useful:
+ when you want to save vidoe stream, but don't have a possibility to fetch video data on client to push it to S3 directly. Saving Safari video stream from a camera is a good example.
+ when you need a proxy server. If you want to preprocess video (or video frames) before the sending it further or run some external services on incoming data.

# TODO:
1. ? format video
2. handle client close connection
3. re-send on appropriate S3 enpoint
   + install S3 cli or make plain #request (better)
   + no file > close connection > crash
   + save temmp file:
     + check if file is ok
     + if ok: upload, delete
     + if not ok: bad response, delete file
