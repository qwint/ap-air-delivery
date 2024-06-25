import http.server
import socketserver

PORT = 80


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        if self.path in ["/", "/pico-window.js", "pico8-gpio-listener.js"]:
            super().do_GET()


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
