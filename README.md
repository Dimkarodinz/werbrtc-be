Example WEBRTC server application.
Simulate one peer, save incoming flow into temp video file, sends it to S3

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
