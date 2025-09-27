#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import signal
import argparse
from pathlib import Path

class SimpleFileWatcher:
    def __init__(self, watch_dir="."):
        self.watch_dir = Path(watch_dir).resolve()
        self.last_modified = {}
        self.update_file_times()

    def update_file_times(self):
        """Update the dictionary of file modification times"""
        for py_file in self.watch_dir.glob("**/*.py"):
            try:
                self.last_modified[str(py_file)] = py_file.stat().st_mtime
            except OSError:
                pass

    def check_for_changes(self):
        """Check if any Python files have been modified"""
        changed_files = []

        # Check existing files for modifications
        for file_path, last_time in list(self.last_modified.items()):
            try:
                current_time = Path(file_path).stat().st_mtime
                if current_time > last_time:
                    changed_files.append(file_path)
                    self.last_modified[file_path] = current_time
            except OSError:
                # File was deleted
                del self.last_modified[file_path]

        # Check for new files
        for py_file in self.watch_dir.glob("**/*.py"):
            file_str = str(py_file)
            if file_str not in self.last_modified:
                changed_files.append(file_str)
                self.last_modified[file_str] = py_file.stat().st_mtime

        return changed_files

class ApartmentCheckerReloader:
    def __init__(self, script_path="apartment_checker_selenium.py", watch_dir="."):
        self.script_path = script_path
        self.watch_dir = Path(watch_dir).resolve()
        self.process = None
        self.debug_mode = False
        self.last_restart = 0
        self.restart_delay = 2  # Minimum seconds between restarts
        self.file_watcher = SimpleFileWatcher(watch_dir)

    def set_debug_mode(self, debug=True):
        """Set whether to run in debug mode (single run) or continuous mode"""
        self.debug_mode = debug

    def start_apartment_checker(self):
        """Start the apartment checker process"""
        if self.process:
            self.stop_apartment_checker()

        print(f"🚀 Starting apartment checker {'(debug mode)' if self.debug_mode else '(continuous mode)'}...")
        sys.stdout.flush()

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
                bufsize=0
            )
            print(f"✅ Process started (PID: {self.process.pid})")
            sys.stdout.flush()
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

def main():
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
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start initial process
        reloader.start_apartment_checker()

        # Main monitoring loop
        while True:
            # Check for file changes
            changed_files = reloader.file_watcher.check_for_changes()
            if changed_files:
                print(f"📝 Files changed: {', '.join([os.path.basename(f) for f in changed_files])}")
                reloader.restart_apartment_checker()

            # Monitor process output and status
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

            time.sleep(1)  # Check every second

    except KeyboardInterrupt:
        print("\\n🛑 Interrupted by user")
    finally:
        reloader.stop_apartment_checker()

if __name__ == "__main__":
    main()