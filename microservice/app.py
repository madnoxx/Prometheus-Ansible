import http.server
import socketserver
import os
from prometheus_client import Info, generate_latest, REGISTRY

# 1. Определение Метрики
host_info = Info('host_info', 'Information about the host environment')

# 2. Определение Типа Хоста
deployment_type_env = os.environ.get('HOST_DEPLOYMENT_TYPE', '').lower()

if deployment_type_env == 'container':
    deployment_type = 'container'
    print(f"Host type determined by environment variable: {deployment_type}")
elif deployment_type_env == 'vm':
    deployment_type = 'virtual_machine'
    print(f"Host type determined by environment variable: {deployment_type}")
else:
    deployment_type = 'physical'
    print(f"HOST_DEPLOYMENT_TYPE not set or invalid ('{deployment_type_env}'), defaulting to: {deployment_type}")

host_info.info({'type': deployment_type})

# 3. Создание Обработчика HTTP Запросов
class MetricsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            try:
                output = generate_latest(REGISTRY)
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
                self.send_header('Content-Length', str(len(output)))
                self.end_headers()
                self.wfile.write(output)
            except Exception as e:
                print(f"Error generating metrics: {e}")
                self.send_error(500, f"Error generating metrics: {e}")
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = """
            <html><head><title>My Microservice</title></head>
            <body>
                <h1>Hello!</h1>
                <p>This is a simple microservice.</p>
                <p>Prometheus metrics are available at <a href='/metrics'>/metrics</a>.</p>
            </body></html>
            """
            self.wfile.write(html_content.encode('utf-8'))


# 4. Запуск HTTP Сервера
if __name__ == "__main__":
    PORT = 8080
    httpd = socketserver.ThreadingTCPServer(("", PORT), MetricsHandler)

    print(f"Serving Prometheus metrics on port {PORT}")
    print(f"Host type determined as: {deployment_type}")
    print(f"Access metrics at http://localhost:{PORT}/metrics")
    print("Press Ctrl+C to exit.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
        httpd.server_close()
        print("Server shut down.")
