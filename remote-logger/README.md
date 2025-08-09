# renote-logger
This project provides a very simple logging service. It was designed and built to allow a remote, wirelessly connected application (such as one running on a Raspberry Pi Pico W) to send its console output to a remote location for viewing.

# Capabilities
It can accept either `text/plain` or `application/json` as the body content type (as defined by the `Content-Type` header).

It prints whatever it receives to the console.

Note that if a json object is sent as `{"message": "blah"}`, then only blah is printed, otherwise the raw stringified JSON is printed.

# Building and running
To build this project it is recommended to use node v22.

It is a standard node / Typescript project, first install the dependencies with:
```
npm install
```

You can build and run the project with:
```
npm run build
node build/index.js
```

However, for development it is better to use:
```
npm run dev
```
This will run the server and monitor the project folder. Any change will trigger a new build and a restart of the server.

You can then send logs to `http://<server>:3002/log`. The port can be set with the `LOGGER_PORT` environment variable.


