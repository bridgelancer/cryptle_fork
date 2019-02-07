from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import socketserver
import subprocess
import sys
import time
import webbrowser

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


# Get script configs from environment
DOC_DIR = os.environ.get('DOC_DIR', '.')
BUILD_DIR = os.environ.get('BUILD_DIR', '_build')
HTML_DIR = os.environ.get('HTML_DIR', 'html')


class DocsHandler(PatternMatchingEventHandler):
    def on_any_event(self, event):
        # todo(alan) logging instead of print
        print(f'* {event.event_type}: {event.src_path}')
        subprocess.run('make html'.split())


# We're not using Python3.7 so here's an exact copy of the source code
class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', '-p', default=4000)

    args = parser.parse_args()

    event_handler = DocsHandler(patterns=['*.py', '*.md', '*.rst'])
    observer = Observer()
    observer.schedule(event_handler, path=DOC_DIR, recursive=True)

    os.chdir('/'.join((DOC_DIR, BUILD_DIR, HTML_DIR)))

    with ThreadingHTTPServer((args.host, args.port), SimpleHTTPRequestHandler) as httpd:
        print('* ===== Watchdog started =====')
        observer.start()
        try:
            webbrowser.open(f'http://{args.host}:{args.port}/')
            while True:
                httpd.handle_request()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print('\r* terminating...')
            observer.stop()
        observer.join()
        print('* ===== Watchdog terminated =====')

    sys.exit(0)
