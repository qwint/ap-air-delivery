import http.server
import socketserver

PORT = 80


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        if self.path.startswith("/?") or self.path in ["/", "/pico-window.js", "/pico8-gpio-listener.js", "/index.js"]:
            super().do_GET()
        # else:
        #     raise Exception(f"Path {self.path} denied")


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
