#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ApartmentCheckerReloader:
    def __init__(self, script_path="apartment_checker_selenium.py", watch_dir="."):
        self.script_path = script_path
        self.watch_dir = Path(watch_dir).resolve()
        self.process = None
        self.observer = None
        self.debug_mode = False
        self.last_restart = 0
        self.restart_delay = 2  # Minimum seconds between restarts

    def set_debug_mode(self, debug=True):
        """Set whether to run in debug mode (single run) or continuous mode"""
        self.debug_mode = debug

    def start_apartment_checker(self):
        """Start the apartment checker process"""
        if self.process:
            self.stop_apartment_checker()

        print(f"🚀 Starting apartment checker {'(debug mode)' if self.debug_mode else '(continuous mode)'}...")

        # Build command
        cmd = [sys.executable, self.script_path]
        if self.debug_mode:
            cmd.append("--debug")
        else:
            cmd.append("--continuous")

        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=self.watch_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            print(f"✅ Process started (PID: {self.process.pid})")
            self.last_restart = time.time()
            return True
        except Exception as e:
            print(f"❌ Failed to start process: {e}")
            return False

    def stop_apartment_checker(self):
        """Stop the apartment checker process"""
        if self.process:
            print(f"🛑 Stopping process (PID: {self.process.pid})...")
            try:
                # Graceful shutdown
                self.process.terminate()

                # Wait for graceful shutdown, then force kill if needed
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("⚠️ Process didn't terminate gracefully, force killing...")
                    self.process.kill()
                    self.process.wait()

                print("✅ Process stopped")
            except Exception as e:
                print(f"⚠️ Error stopping process: {e}")
            finally:
                self.process = None

    def restart_apartment_checker(self):
        """Restart the apartment checker process with rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_restart

        if time_since_last < self.restart_delay:
            wait_time = self.restart_delay - time_since_last
            print(f"⏳ Rate limiting: waiting {wait_time:.1f}s before restart...")
            time.sleep(wait_time)

        print("🔄 Restarting apartment checker due to file changes...")
        self.start_apartment_checker()

    def read_output(self):
        """Read and display output from the apartment checker process"""
        if not self.process:
            return

        try:
            # Non-blocking read
            if self.process.poll() is None:  # Process is still running
                while True:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    print(f"📊 {line.rstrip()}")
        except Exception as e:
            print(f"⚠️ Error reading output: {e}")

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, reloader):
        self.reloader = reloader
        self.last_modified = {}

    def should_trigger_restart(self, event):
        """Determine if this file change should trigger a restart"""
        if event.is_directory:
            return False

        # Only watch Python files
        if not event.src_path.endswith('.py'):
            return False

        # Ignore temporary files and hidden files
        filename = os.path.basename(event.src_path)
        if filename.startswith('.') or filename.endswith('.tmp') or filename.endswith('.pyc'):
            return False

        # Rate limiting: ignore rapid successive changes to the same file
        current_time = time.time()
        last_time = self.last_modified.get(event.src_path, 0)
        if current_time - last_time < 1:  # Ignore changes within 1 second
            return False

        self.last_modified[event.src_path] = current_time
        return True

    def on_modified(self, event):
        if self.should_trigger_restart(event):
            print(f"📝 File changed: {os.path.relpath(event.src_path)}")
            self.reloader.restart_apartment_checker()

    def on_created(self, event):
        if self.should_trigger_restart(event):
            print(f"📄 File created: {os.path.relpath(event.src_path)}")
            self.reloader.restart_apartment_checker()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Live-reloading apartment checker')
    parser.add_argument('--debug', action='store_true',
                       help='Run in debug mode (single runs instead of continuous)')
    parser.add_argument('--script', default='apartment_checker_selenium.py',
                       help='Script to watch and run (default: apartment_checker_selenium.py)')
    parser.add_argument('--watch-dir', default='.',
                       help='Directory to watch for changes (default: current directory)')
    args = parser.parse_args()

    # Check if script exists
    if not os.path.exists(args.script):
        print(f"❌ Script not found: {args.script}")
        sys.exit(1)

    # Create reloader
    reloader = ApartmentCheckerReloader(args.script, args.watch_dir)
    reloader.set_debug_mode(args.debug)

    # Set up file watching
    event_handler = FileChangeHandler(reloader)
    observer = Observer()
    observer.schedule(event_handler, args.watch_dir, recursive=True)

    print("🔍 Live Apartment Checker Reloader")
    print("=" * 50)
    print(f"📁 Watching directory: {Path(args.watch_dir).resolve()}")
    print(f"🐍 Script: {args.script}")
    print(f"🎯 Mode: {'Debug (single runs)' if args.debug else 'Continuous'}")
    print("📝 Will restart on .py file changes")
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 50)

    def signal_handler(signum, frame):
        print("\\n🛑 Shutting down...")
        reloader.stop_apartment_checker()
        observer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start watching for file changes
        observer.start()

        # Start initial process
        reloader.start_apartment_checker()

        # Main loop - monitor output and keep running
        while True:
            if reloader.debug_mode and reloader.process:
                # In debug mode, wait for process to finish then restart
                if reloader.process.poll() is not None:
                    print("✅ Debug run completed, waiting for file changes...")
                    reloader.process = None
                else:
                    reloader.read_output()
            else:
                # In continuous mode, just monitor output
                reloader.read_output()

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\\n🛑 Interrupted by user")
    finally:
        reloader.stop_apartment_checker()
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()