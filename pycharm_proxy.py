import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import socket
from http import HTTPStatus

import select


class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def do_PUT(self):
        self.handle_request()

    def do_DELETE(self):
        self.handle_request()

    def do_CONNECT(self):
        self.handle_connect()

    def handle_request(self):
        url = self.path

        if self.should_block_request(url):
            self.send_error(HTTPStatus.FORBIDDEN, "Request blocked by proxy")
            return

        try:
            with urllib.request.urlopen(url) as response:
                self.send_response(response.status)
                self.send_headers(response)
                self.wfile.write(response.read())
        except urllib.error.HTTPError as e:
            self.send_error(e.code, e.reason)
        except urllib.error.URLError as e:
            self.send_error(HTTPStatus.BAD_GATEWAY, str(e.reason))

    def handle_connect(self):
        self.send_response(200, 'Connection Established')
        self.end_headers()

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host, port = self.path.split(':')
        conn.connect((host, int(port)))

        self.connection.setblocking(False)
        conn.setblocking(False)

        try:
            while True:
                read_sockets, _, _ = select.select([self.connection, conn], [], [])
                if self.connection in read_sockets:
                    data = self.connection.recv(4096)
                    if len(data) == 0:
                        break
                    conn.sendall(data)
                if conn in read_sockets:
                    data = conn.recv(4096)
                    if len(data) == 0:
                        break
                    self.connection.sendall(data)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
            self.connection.close()

    def should_block_request(self, url):
        blocked_domains = ["jetbrains.com", "tabnine.com", "intellij.net"]
        for domain in blocked_domains:
            if domain in url:
                return True
        return False

    def send_headers(self, response):
        for header in response.getheaders():
            self.send_header(header[0], header[1])
        self.end_headers()


def run(server_class=http.server.HTTPServer, handler_class=ProxyHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting proxy server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
